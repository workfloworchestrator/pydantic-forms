# Installation

Pydantic Forms is published on PyPI as [`pydantic-forms`](https://pypi.org/project/pydantic-forms).

```sh
uv add pydantic-forms
```

## Extras

- `fastapi` — the FastAPI exception handler in `pydantic_forms.exception_handlers.fastapi`
- `orjson` — use `orjson` instead of the standard library `json` module for (de)serialization

```sh
uv add "pydantic-forms[fastapi,orjson]"
```
