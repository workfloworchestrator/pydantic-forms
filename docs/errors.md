# Errors

All exceptions live in `pydantic_forms.exceptions` and subclass `FormException`.

| Exception | Raised when | FastAPI status code |
|---|---|---|
| `FormNotCompleteError` | The wizard has more pages left; carries the next page's JSON schema (`.form`) and, if the page defines any, its [page metadata](usage.md#page-metadata) (`.meta`, otherwise `None`). | 510 Not Extended |
| `FormValidationError` | Submitted input failed Pydantic validation; carries the translated errors (`.errors`). | 400 Bad Request |
| `FormOverflowError` | More inputs were submitted than the wizard has pages for. | 500 Internal Server Error |
| `FormNotFoundError` | `start_form` was called with a key that no form is registered under. | 404 Not Found |

## FastAPI response shapes

The `form_error_handler` (see [FastAPI integration](usage.md#fastapi-integration)) turns these into JSON responses with
the status codes listed above. Any other `FormException` results in a 500 Internal Server Error.

Set the `LOG_LEVEL_PYDANTIC_FORMS=DEBUG` environment variable to include a `traceback` field in the 400 and 510
responses and in the logs.
