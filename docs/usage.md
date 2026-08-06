# Usage

## Defining a form

A form page is a `FormPage`, a `pydantic.BaseModel` subclass. Its fields become the inputs the frontend renders,
using either plain Python/Pydantic types or the [field types](fields.md) this library provides:

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
