from typing import cast, List, Dict, Any, TypedDict, Union

from pydantic_forms.types import InputForm, JSON


class FormException(Exception):
    pass


class FormNotCompleteError(FormException):
    form: InputForm

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
            f"{display_errors(cast(List[Dict[str, Any]], self.errors))}"  # type: ignore
        )
