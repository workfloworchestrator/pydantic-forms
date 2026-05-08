# Required field handling

Pydantic considers a field *required* only when it has no default value. That works for an API payload, but a `FormPage` is also used to *transmit* data: a field with a default is still something the user is expected to confirm before submitting. Pydantic Forms therefore offers a stricter mode that promotes such fields to required.

## Two modes

The behavior is controlled by the `REQUIRED_FIELD_HANDLING` setting (read from the environment via `pydantic-settings`):

| Mode | Behavior |
|---|---|
| `default` | Pydantic's native rule — a field is required only when it has no default. |
| `extended` | A field is also required when it has a non-`None` default (or `default_factory`), unless it's optional/nullable or marked as display-only. |

Default is `default`. Switch by setting:

```shell
export REQUIRED_FIELD_HANDLING=extended
```

## Example

```python
from pydantic_forms.core import FormPage


class MyForm(FormPage):
    name: str  # required in both modes
    age: int = 18  # required only in extended
    nickname: str | None = None  # never required
```

The schema's `required` list expands accordingly:

- `default` mode → `["name"]`
- `extended` mode → `["name", "age"]`
