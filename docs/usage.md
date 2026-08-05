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
def create_service_form(state):
    user_input = yield CreateServiceForm

    class ConfirmForm(FormPage):
        service_name: str = user_input.service_name

    yield ConfirmForm

    return user_input.model_dump()
```

`post_form` drives a generator with a list of submitted inputs (one dict per page) and returns the final result:

```python
from pydantic_forms.core import post_form

result = post_form(
    create_service_form,
    state={},
    user_inputs=[
        {"service_name": "svc-1", "service_speed": "1000"},
        {},  # Empty input suffices for the ConfirmForm
    ],
)
```

Passing fewer inputs than the wizard has pages — an empty list for the very first request — raises
`FormNotCompleteError` carrying the JSON schema of the next page instead. That is the normal flow: a frontend keeps
posting the inputs it has collected so far, and each response tells it what to render next.

`generate_form` wraps `post_form` and returns the next page's JSON schema (or `None` once the form is done) instead
of raising:

```python
from pydantic_forms.core import generate_form

schema = generate_form(create_service_form, state={}, user_inputs=[])
```

Both are low-level: they need the generator object itself. Applications normally register forms by name and expose
them through a single endpoint — see [FastAPI integration](#fastapi-integration).

### Registering forms

`register_form` associates a generator with a key. `start_form` then resolves that key, seeds the initial state and
hands off to `post_form`:

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

## Async

An async equivalent lives in `pydantic_forms.core.asynchronous`, with the same `post_form`, `generate_form` and
`start_form` functions, for generators defined with `async def` and `yield`.

One difference matters: an async generator cannot `return` a value, so the final result is **yielded** instead of
returned. Writing `return user_input.model_dump()` in an `async def` generator is a `SyntaxError`:

```python
import asyncio

from pydantic_forms.core.asynchronous import post_form


async def create_service_form(state):
    user_input = yield CreateServiceForm
    yield user_input.model_dump()  # yield, not return


result = asyncio.run(
    post_form(
        create_service_form,
        state={},
        user_inputs=[{"service_name": "svc-1", "service_speed": "1000"}],
    )
)
```

Use `asyncio.run` only at the outermost level; inside a FastAPI endpoint you would simply `await post_form(...)`.

## FastAPI integration

### The form endpoint

One endpoint serves every registered form:

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
