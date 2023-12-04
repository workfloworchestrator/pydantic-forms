import traceback
from typing import Any, Iterable, TypedDict, Union, cast

from more_itertools import side_effect
from pydantic import ValidationError
from pydantic_core import ErrorDetails

from pydantic_forms.types import JSON


class FormException(Exception):  # noqa: N818
    pass


class FormNotCompleteError(FormException):
    """Raised when fewer inputs are provided than the form can process.

    This exception is part of the normal forms workflow.
    """

    form: JSON

    def __init__(self, form: JSON):
        super().__init__(form)
        self.form = form


class FormOverflowError(FormException):
    """Raised when more inputs are provided than the form can process."""


def convert_errors(validation_error: ValidationError) -> Iterable[ErrorDetails]:
    """Convert Pydantic's error messages to our needs.

    https://docs.pydantic.dev/2.4/errors/errors/#customize-error-messages
    """

    def convert_error(error: ErrorDetails) -> None:
        exc = error.get("ctx", {}).get("error")
        if isinstance(exc, ValueError):
            # Removes the "Value error, " prefix from the msg
            error["msg"] = str(exc)
        if error["loc"] == ():
            # Reinstate the "__root__" location for validation errors raised by Pydantic v1's root_validator.
            # With Pydantic v2's model_validator the location is an empty string, which breaks frontend clients.
            error["loc"] = ("__root__",)
        return

    return side_effect(convert_error, validation_error.errors())


class FormValidationError(FormException):
    validator_name: str
    errors: list[ErrorDetails]

    def __init__(self, validator_name: str, error: ValidationError):
        super().__init__()
        self.validator_name = validator_name
        self.errors = list(convert_errors(error))

    def __str__(self) -> str:
        no_errors = len(self.errors)
        return (
            f'{no_errors} validation error{"" if no_errors == 1 else "s"} for {self.validator_name}\n'
            f"{display_errors(cast(list[ErrorDict], self.errors))}"
        )


Loc = tuple[Union[int, str], ...]


class _ErrorDictRequired(TypedDict):
    loc: Loc
    msg: str
    type: str


class ErrorDict(_ErrorDictRequired, total=False):
    ctx: dict[str, Any]


def display_errors(errors: list["ErrorDict"]) -> str:
    return "\n".join(f'{_display_error_loc(e)}\n  {e["msg"]} ({_display_error_type_and_ctx(e)})' for e in errors)


def _display_error_loc(error: "ErrorDict") -> str:
    return " -> ".join(str(e) for e in error["loc"])


def _display_error_type_and_ctx(error: "ErrorDict") -> str:
    t = "type=" + error["type"]
    ctx = error.get("ctx")
    if ctx:
        return t + "".join(f"; {k}={v}" for k, v in ctx.items())
    return t


def show_ex(ex: Exception, stacklimit: Union[int, None] = None) -> str:
    """Show an exception, including its class name, message and (limited) stacktrace.

    >>> try:
    ...     raise Exception("Something went wrong")
    ... except Exception as e:
    ...     print(show_ex(e))
    Exception: Something went wrong
    ...
    """
    tbfmt = "".join(traceback.format_tb(ex.__traceback__, stacklimit))
    return "{}: {}\n{}".format(type(ex).__name__, ex, tbfmt)
