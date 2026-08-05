# Errors

All exceptions live in `pydantic_forms.exceptions` and subclass `FormException`.

| Exception | Raised when |
|---|---|
| `FormNotCompleteError` | The wizard has more pages left; carries the next page's JSON schema (`.form`). |
| `FormValidationError` | Submitted input failed Pydantic validation; carries the translated errors (`.errors`). |
| `FormOverflowError` | More inputs were submitted than the wizard has pages for. |
| `FormNotFoundError` | `start_form` was called with a key that no form is registered under. |

## FastAPI response shapes

The `form_error_handler` (see [FastAPI integration](usage.md#fastapi-integration)) turns these into JSON responses with the following status codes:

- `FormValidationError`: 400 Bad Request
- `FormNotFoundError`: 404 Not Found
- `FormExceptions` (i.e. `FormOverflowError`): 500 Internal Server Error
- `FormNotCompleteError`: 510 Not Extended

Set the `LOG_LEVEL_PYDANTIC_FORMS=DEBUG` environment variable to include a `traceback` field in the 400 and 510
responses and in the logs.
