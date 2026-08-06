# How it works

The main logic is implemented in `post_form` which validates each submitted form page and decides whether the
wizard is finished, or if an error should be returned. Instead of interacting with it directly, applications
should typically use the wrapper `start_form` or in some cases `generate_form`.

## post_form

`post_form` takes the generator function itself, an initial state, and one input dict per page:

```python
from pydantic_forms.core import FormPage, post_form
from pydantic_forms.types import FormGenerator, State


class CreateServiceForm(FormPage):
    service_name: str


def create_service_form(state: State) -> FormGenerator:
    user_input = yield CreateServiceForm
    return user_input.model_dump()


result = post_form(
    create_service_form,
    state={},
    user_inputs=[{"service_name": "svc-1"}],
)
```

```pycon
>>> result
{'service_name': 'svc-1'}
```

### The generator protocol

A form generator is an ordinary Python generator, and `post_form` drives it like a coroutine:

1. It calls the generator function with the initial state and sends `None` to reach the first `yield`. What comes
   back is a `FormPage` subclass: the page to render.
2. It takes the first submitted input off the list and validates it against that page. A failure raises
   `FormValidationError` carrying the translated Pydantic errors.
3. The validated model is merged into the state and sent back into the generator, where it becomes the value of the
   `yield` expression. The generator runs on until its next `yield`, so it can branch on what the user just
   submitted.
4. Steps 2 and 3 repeat until either the inputs or the pages run out.

If the pages run out first, the generator's return value is the result of the whole wizard. If there are still
inputs left once the generator has finished, `post_form` raises `FormOverflowError`.

If the inputs run out first, the page that is currently pending is converted to a JSON schema and raised as
`FormNotCompleteError`:

```pycon
>>> post_form(create_service_form, state={}, user_inputs=[])
Traceback (most recent call last):
  ...
pydantic_forms.exceptions.FormNotCompleteError: {...}
```

That is the normal flow: a frontend keeps posting the inputs it has collected so far, and each response tells it
what to render next.

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
instead of `send`. Because an async generator cannot return a value the result is yielded instead, and `post_form`
treats a yielded `dict` as the end of the wizard. Also see [Async](usage.md#async).
