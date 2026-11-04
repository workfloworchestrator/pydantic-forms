# How it works

The core function is `walk_form`, which validates each submitted form page and says where the wizard stands: the
next page, the result, or a rejected page. A program that reads a form uses it directly, together with `page_schema`.

Three wrappers build on it:

- `post_form` turns those endings into a return value and two exceptions, for use in an API.
- `start_form` looks a form up by its registered key and calls `post_form`; this is what an application's endpoint
  calls.
- `generate_form` calls `post_form` and returns the next page's JSON schema rather than raising, or `None` once the
  wizard is done.

## walk_form

`walk_form` takes the generator function itself, an initial state, and one input dict per page, and returns where
the walk ended:

```python
from pydantic_forms.core import Complete, FormPage, NextPage, Rejected, walk_form
from pydantic_forms.types import FormGenerator, State


class CreateServiceForm(FormPage):
    service_name: str


def create_service_form(state: State) -> FormGenerator:
    user_input = yield CreateServiceForm
    return user_input.model_dump()


outcome = walk_form(create_service_form, state={}, user_inputs=[])
```

The three endings are `NextPage`, with the page model and its index, `Complete`, with the result, and `Rejected`,
with the page that did not validate, its index, and a `FormValidationError` carrying the translated Pydantic errors:

```pycon
>>> outcome
NextPage(model=<class '...CreateServiceForm'>, index=0)
>>> walk_form(create_service_form, state={}, user_inputs=[{"service_name": "svc-1"}])
Complete(state={'service_name': 'svc-1'})
>>> rejected = walk_form(create_service_form, state={}, user_inputs=[{"service_name": 42}])
>>> rejected.index, rejected.error.errors[0]["msg"]
(0, 'Input should be a valid string')
```

This is the entry point for a program that reads a form, such as an agent filling it in: it wants the pending page
as a model to inspect rather than as a schema to render, and a rejected page told apart from a failure.

### The generator protocol

A form generator is an ordinary Python generator, and `walk_form` drives it like a coroutine:

1. It calls the generator function with the initial state and sends `None` to reach the first `yield`. What comes
   back is a `FormPage` subclass: the page to render.
2. It takes the first submitted input off the list and validates it against that page. A failure ends the walk in
   `Rejected`.
3. The validated model is merged into the state and sent back into the generator, where it becomes the value of the
   `yield` expression. The generator runs on until its next `yield`, so it can branch on what the user just
   submitted.
4. Steps 2 and 3 repeat until either the inputs or the pages run out.

If the inputs run out first, the walk ends in `NextPage` with the page that is currently pending. If the pages run
out first, the generator's return value is the result of the whole wizard, and the walk ends in `Complete`. If there
are still inputs left once the generator has finished, `walk_form` raises `FormOverflowError`: that is a caller's
mistake, not an ending of the form.

## post_form

`post_form` is a thin wrapper around `walk_form` for use in an API. It makes the same walk and turns the three endings
into a return value and two exceptions: `Complete` is returned as the result, `Rejected` raises its
`FormValidationError`, and `NextPage` converts the pending page to a JSON schema and raises it as
`FormNotCompleteError`.

```python
from pydantic_forms.core import post_form

result = post_form(
    create_service_form,
    state={},
    user_inputs=[{"service_name": "svc-1"}],
)
```

```pycon
>>> result
{'service_name': 'svc-1'}
>>> post_form(create_service_form, state={}, user_inputs=[])
Traceback (most recent call last):
  ...
pydantic_forms.exceptions.FormNotCompleteError: {...}
```

That is the normal flow: a frontend keeps posting the inputs it has collected so far, and each response tells it
what to render next. `FormOverflowError` passes through unchanged.

## A page for a program

A frontend renders the schema `post_form` raises. A program can read the same schema, and `page_schema` gives it the
page as one self-contained document:

```python
from pydantic_forms.core import form_errors, page_schema

schema = page_schema(CreateServiceForm, inline_refs=True)
```

```pycon
>>> schema["properties"]["service_name"]
{'title': 'Service Name', 'type': 'string'}
>>> schema["required"]
['service_name']
```

JSON Schema already says most of what a program needs: `type`, `enum`, `format`, `default`, `required`, and the
length and range keywords. Four things make it sufficient:

- `inline_refs=True` replaces every `$ref` with the definition it points to, so a choice or a nested model is read in
  place. Only a model that contains itself keeps its reference, with its definition under `$defs`.
- A field that is shown and never submitted carries the standard `readOnly: true`: a label, a divider, a summary
  table, a read-only value. Submit nothing for it.
- A `Choice` lists its values in `enum` and, where they differ from what a person sees, the labels in `options`.
  Submit the value. An `Accept` field lists `ACCEPTED` and `INCOMPLETE` for the checkbox that renders it; only
  `ACCEPTED` passes validation.
- A field whose options are fetched from an endpoint says where in `optionsSource`, see
  [Usage](usage.md#fields-whose-options-come-from-an-endpoint). `options_sources` lists a page's sourced fields by
  their location in the schema, nested models and list items included.

```python
from typing import Annotated

from pydantic_forms.utils.schema import options_sources
from pydantic_forms.validators import OptionsSource


class PickLocationForm(FormPage):
    location: Annotated[str, OptionsSource(url="/api/locations")]
```

```pycon
>>> options_sources(page_schema(PickLocationForm))
{'/properties/location': {'url': '/api/locations'}}
```

`form_errors` is the verdict on a rejected page as data: one entry per message, with its location on the page,
translated the way the frontend shows it:

```pycon
>>> form_errors(rejected.error)
[FormFieldError(loc=['service_name'], msg='Input should be a valid string', type='string_type')]
```

## The wrappers

### start_form

`start_form` looks the generator up by key in the registry that `register_form` fills, seeds the initial state with
that key plus any extra keyword arguments it was given, and then calls `post_form`. An unknown key raises
`FormNotFoundError`. This is the one an application's endpoint calls, so it is covered in
[Registering forms](usage.md#registering-forms).

### generate_form

`generate_form` calls `post_form` and catches that exception, so it returns the next page's JSON schema rather than
raising, and `None` once there is nothing left to render.

That makes it the one to reach for when the schema is *data* rather than the response itself: embedding the pending
form in a larger payload while serving a suspended process, or stepping through a wizard from a read-only endpoint
and using `None` to detect completion. A submit endpoint should use `start_form` instead and let the exception
handler turn `FormNotCompleteError` into its 510 response.

```python
from pydantic_forms.core import generate_form

schema = generate_form(create_service_form, state={}, user_inputs=[])
```

```pycon
>>> schema["required"]
['service_name']
>>> schema["properties"]
{'service_name': {'title': 'Service Name', 'type': 'string'}}
```

Once every page has been submitted there is nothing left to render, and the return value is `None`:

```pycon
>>> generate_form(
...     create_service_form, state={}, user_inputs=[{"service_name": "svc-1"}]
... ) is None
True
```

## Async

The variants in `pydantic_forms.core.asynchronous` work the same way, interacting with the generator through `asend`
instead of `send`. Because an async generator cannot return a value the result is yielded instead, and the async
`walk_form` treats a yielded `dict` as the end of the wizard, ending in the same three outcomes; `post_form` wraps it
the same way. Also see [Async](usage.md#async).
