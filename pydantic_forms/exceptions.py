import traceback
from typing import Any, Dict, List, Tuple, TypedDict, Union, cast

from pydantic_forms.types import JSON

# from pydantic_forms.types import InputForm


class FormException(Exception):
    pass


class FormNotCompleteError(FormException):
    # form: InputForm  # TODO this is a basemodel but it's initialized to JSON
    form: JSON

    def __init__(self, form: JSON):
        super().__init__(form)
        self.form = form


class PydanticErrorDict(TypedDict):
    loc: List[Union[str, int]]
    type: str
    msg: str
    ctx: Dict[str, Any]


class FormValidationError(FormException):
    validator_name: str
    errors: List[PydanticErrorDict]

    def __init__(self, validator_name: str, errors: List[Dict[str, Any]]):
        super().__init__(validator_name, errors)
        self.validator_name = validator_name
        self.errors = cast(List[PydanticErrorDict], errors)

    def __str__(self) -> str:
        no_errors = len(self.errors)
        return (
            f'{no_errors} validation error{"" if no_errors == 1 else "s"} for {self.validator_name}\n'
            f"{display_errors(cast(List[ErrorDict], self.errors))}"
        )


Loc = Tuple[Union[int, str], ...]


class _ErrorDictRequired(TypedDict):
    loc: Loc
    msg: str
    type: str


class ErrorDict(_ErrorDictRequired, total=False):
    ctx: Dict[str, Any]


def display_errors(errors: List["ErrorDict"]) -> str:
    return "\n".join(f'{_display_error_loc(e)}\n  {e["msg"]} ({_display_error_type_and_ctx(e)})' for e in errors)


def _display_error_loc(error: "ErrorDict") -> str:
    return " -> ".join(str(e) for e in error["loc"])


def _display_error_type_and_ctx(error: "ErrorDict") -> str:
    t = "type=" + error["type"]
    ctx = error.get("ctx")
    if ctx:
        return t + "".join(f"; {k}={v}" for k, v in ctx.items())
    else:
        return t


def show_ex(ex: Exception, stacklimit: Union[int, None] = None) -> str:
    """
    Show an exception, including its class name, message and (limited) stacktrace.

    >>> try:
    ...     raise Exception("Something went wrong")
    ... except Exception as e:
    ...     print(show_ex(e))
    Exception: Something went wrong
    ...
    """
    tbfmt = "".join(traceback.format_tb(ex.__traceback__, stacklimit))
    return "{}: {}\n{}".format(type(ex).__name__, ex, tbfmt)
