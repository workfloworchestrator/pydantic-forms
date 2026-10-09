# Usage

## Defining a form

A form page is a `FormPage`, a `pydantic.BaseModel` subclass. Its fields become the inputs the frontend renders,
using either plain Python/Pydantic types or the [field types](examples.md#field-types) this library provides:

```python
from pydantic_forms.core import FormPage
from pydantic_forms.types import strEnum


class Speed(strEnum):
    _1000 = "1000"
    _10000 = "10000"


class CreateServiceForm(FormPage):
    service_name: str
    service_speed: Speed
```

## Form wizards

A form generator is a function that `yield`s one `FormPage` subclass at a time. Each `yield` blocks until the
corresponding page's input has been validated; the validated data is sent back into the generator, and the return
value is the combined result once there are no more pages:

```python
from pydantic_forms.types import FormGenerator, State


def create_service_form(state: State) -> FormGenerator:
    user_input = yield CreateServiceForm

    class ConfirmForm(FormPage):
        service_name: str = user_input.service_name

    yield ConfirmForm

    return user_input.model_dump()
```

You don't call this generator yourself but register it under a key for `start_form` to access it, as shown in the
next section. Read [How it works](how-it-works.md) for details about the machinery.

### Registering forms

`register_form` associates a generator with a key. `start_form` then resolves that key, seeds the initial state and
iterates over the user inputs:

```python
from pydantic_forms.core import register_form, start_form

register_form("create_service", create_service_form)

result = start_form(
    "create_service",
    user_inputs=[
        {"service_name": "svc-1", "service_speed": "1000"},
        {},  # Empty input suffices for the ConfirmForm
    ],
)
```

The result is whatever the generator returned, with every value already validated and coerced to its annotated
type:

```pycon
>>> result["service_name"]
'svc-1'
>>> result["service_speed"]
<Speed._1000: '1000'>
```

Omitting the second `{}` from the user input would produce a `FormNotCompleteError`.

## Async

An async equivalent lives in `pydantic_forms.core.asynchronous`, with the same `post_form`, `generate_form` and
`start_form` functions, for generators defined with `async def` and `yield`.

One difference matters: an async generator cannot `return` a value, so the final result is **yielded** instead of
returned. Writing `return user_input.model_dump()` in an `async def` generator is a `SyntaxError`:

```python
from pydantic_forms.types import FormGeneratorAsync


async def create_service_form(state: State) -> FormGeneratorAsync:
    user_input = yield CreateServiceForm
    yield user_input.model_dump()  # yield, not return
```

Note the return type: `FormGeneratorAsync` rather than `FormGenerator`, since the result is yielded rather than
returned.

Register it exactly as above; the endpoint in the next section awaits `start_form` to drive it.

## FastAPI integration

### An example endpoint

An example of how you can hook up the form wizard in an API:

```python
from typing import Any

from fastapi import APIRouter

from pydantic_forms.core.asynchronous import start_form

router = APIRouter()


@router.post("/{form_key}")
async def new_form(form_key: str, json_data: list[dict[str, Any]]) -> dict[str, Any]:
    return await start_form(form_key, user_inputs=json_data)
```

The frontend posts an empty list to get the first page, then re-posts the accumulated inputs after every step until
the endpoint returns the validated state. Extra keyword arguments to `start_form` land in the generator's initial
`state`.

### Error handling

`form_error_handler` turns `FormNotCompleteError` and `FormValidationError` into the JSON responses a frontend
expects (see [Errors](errors.md)):

```python
from fastapi import FastAPI
from pydantic_forms.exceptions import FormException
from pydantic_forms.exception_handlers.fastapi import form_error_handler

app = FastAPI()
app.add_exception_handler(FormException, form_error_handler)
app.include_router(router)
```

An unknown `form_key` raises `FormNotFoundError`, which the handler reports as a 404.

## Page metadata

Sometimes the frontend needs to know something about a page that its JSON schema cannot express. Setting
`meta__` on a form page attaches arbitrary JSON to the response that carries it:

```python
from typing import ClassVar

from pydantic_forms.types import FormMeta


class ConfirmForm(FormPage):
    meta__: ClassVar[FormMeta] = {"hasNext": False}

    service_name: str
```

It comes back as `.meta` on the `FormNotCompleteError`, and as the `meta` key of the JSON response:

```pycon
>>> from pydantic_forms.core import post_form
>>> from pydantic_forms.exceptions import FormNotCompleteError
>>> def confirm_only(state: State) -> FormGenerator:
...     yield ConfirmForm
...     return {}
...
>>> try:
...     post_form(confirm_only, state={}, user_inputs=[])
... except FormNotCompleteError as exc:
...     exc.meta
...
{'hasNext': False}
```

The value is entirely free-form: this library never looks inside it, it only passes it through, so whatever it
holds is a contract between your own backend and frontend. `FormMeta` documents the well-known keys — `hasNext`
marks whether another page follows, and `customButtons` relabels or restyles the previous/next buttons — but
being `total=False`, it doesn't stop a page from adding further keys of its own.

### Custom buttons

To relabel or restyle the previous/next buttons of a page, add a field with a `ButtonsConfig` as its default.
Each `Button` takes a `text` label and a `color`; set only the buttons and keys you want to change,
and the frontend keeps its defaults for the rest. The config is sent as `customButtons` in the meta of the
page, alongside the rest of its `meta__`, while the field itself stays out of the schema and the validated result:

```python
from pydantic_forms.validators import Button, ButtonsConfig


class ConfirmButtonsForm(FormPage):
    meta__: ClassVar[FormMeta] = {"hasNext": False}

    custom_buttons: ButtonsConfig = ButtonsConfig(
        previous=Button(text="Back"),
        next=Button(text="Confirm", color="danger"),
    )
    confirm: bool
```

```pycon
>>> def buttons_form(state: State) -> FormGenerator:
...     yield ConfirmButtonsForm
...     return {}
...
>>> try:
...     post_form(buttons_form, state={}, user_inputs=[])
... except FormNotCompleteError as exc:
...     exc.meta
...
{'hasNext': False, 'customButtons': {'previous': {'text': 'Back'}, 'next': {'text': 'Confirm', 'color': 'danger'}}}
```

Or set the same overrides as `customButtons` in `meta__` directly:

```python
class ConfirmMetaForm(FormPage):
    meta__: ClassVar[FormMeta] = {
        "hasNext": False,
        "customButtons": {
            "previous": {"text": "Back"},
            "next": {
                "text": "Confirm",
                "color": "danger",
            },
        },
    }

    confirm: bool
```

```pycon
>>> def meta_form(state: State) -> FormGenerator:
...     yield ConfirmMetaForm
...     return {}
...
>>> try:
...     post_form(meta_form, state={}, user_inputs=[])
... except FormNotCompleteError as exc:
...     exc.meta["customButtons"]["next"]
...
{'text': 'Confirm', 'color': 'danger'}
```

Use one or the other, combining them will result in an error. The same goes for using `ButtonsConfig` multiple times.

`meta__` is a `ClassVar`, which keeps it out of the generated schema and out of the validated result: it is
metadata about the page, not a field on it.

## Field layout

By default the frontend stacks every field below the previous one, each taking the full width of the form.
[`Layout`](reference.md#pydantic_forms.validators.Layout) places fields next to each other on a 12-column
grid. It is `Annotated` metadata, so it combines freely with other constraints and with `Field(...)`:

```python
from datetime import date
from typing import Annotated

from pydantic import Field

from pydantic_forms.validators import Layout, LongText


class ProfileForm(FormPage):
    # Row 1: three fields side by side, their spans add up to 12
    full_name: Annotated[str, Layout(span=6)]
    age: Annotated[int, Layout(span=3)]
    birth_date: Annotated[date, Layout(span=3)]

    # Row 2 and 3: the comments take two rows on the left half, the next fields fill the right half
    comments: Annotated[LongText, Layout(span=6, row_span=2)] = Field(title="Comments")
    phone: Annotated[str, Layout(span=6)]
    email: Annotated[str, Layout(span=6)]

    # No Layout: a row of its own
    remarks: str
```

Each option is optional:

| Option     | Default          | Description                                                                      |
|------------|------------------|----------------------------------------------------------------------------------|
| `span`     | 12, full width   | Width of the field in columns, 1-12.                                             |
| `start`    | next free column | Column to start at, 1-12. The columns before it stay empty.                      |
| `new_row`  | `False`          | Always start on a new row, even when the current row has space left.             |
| `row_span` | 1                | Height of the field in rows. The following fields are placed next to it.         |
| `align`    | `"stretch"`      | Vertical position within the row: `"start"`, `"center"`, `"end"` or `"stretch"`. |

`Layout` only adds a `layout` object to the field's JSON schema, using camelCase keys and leaving out the
options that are not set. It does not change validation:

```pycon
>>> ProfileForm.model_json_schema()["properties"]["comments"]["layout"]
{'rowSpan': 2, 'span': 6}
>>> class NoticeForm(FormPage):
...     notice: Annotated[str, Layout(span=6, start=7, new_row=True, align="end")]
...
>>> NoticeForm.model_json_schema()["properties"]["notice"]["layout"]
{'align': 'end', 'newRow': True, 'span': 6, 'start': 7}
```

A field that would not fit on the grid is rejected when the form is defined:

```pycon
>>> Layout(start=10, span=6)
Traceback (most recent call last):
...
ValueError: start + span exceeds the 12 column grid
```

Placing the fields is up to the frontend. The [pydantic-forms npm package](https://www.npmjs.com/package/pydantic-forms)
renders the `layout` on a CSS grid, also inside nested models and list items, where the 12 columns are the width of
the nested object. Fields without a `Layout` take the full width, so existing forms render as before.
