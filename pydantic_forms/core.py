# Copyright 2019-2022 SURF.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from copy import deepcopy
from typing import Any, Optional, Union, List, Generator

import structlog
from pydantic.config import Extra
from pydantic.error_wrappers import ValidationError

# from cim.forms.forms import get_form
from pydantic.fields import Field, Undefined, ModelField
from pydantic.main import BaseModel

from pydantic_forms.exceptions import FormNotCompleteError, FormValidationError
from pydantic_forms.types import InputForm, StateInputFormGenerator, State
from pydantic_forms.utils.json import json_dumps, json_loads


logger = structlog.get_logger(__name__)


def generate_form(
    form_generator: Union[StateInputFormGenerator, None], state: State, user_inputs: List[State]
) -> Union[StateInputFormGenerator, None]:
    """Generate form using form generator as defined by a form definition."""
    try:
        # Generate form is basically post_form
        post_form(form_generator, state, user_inputs)
    except FormNotCompleteError as e:
        # Form is not finished and raises the next form, this is expected
        return e.form

    # Form is finished and thus there is no new form
    return None


def post_form(form_generator: Union[StateInputFormGenerator, None], state: State, user_inputs: List[State]) -> State:
    """Post process user_input based on form definition."""
    # there is no form_generator so we return no validated data
    if not form_generator:
        return {}

    current_state = deepcopy(state)

    logger.debug("Post process form", state=state, user_inputs=user_inputs)

    # Generate generator
    generator = form_generator(current_state)

    try:
        # Generate first form (we need to send None here, since the arguments are already given
        # when we generated the generator)
        generated_form: InputForm = generator.send(None)

        # Loop through user inputs and for each input validate and update current state and validation results
        for user_input in user_inputs:
            # Validate
            try:
                form_validated_data = generated_form(**user_input)
            except ValidationError as e:
                raise FormValidationError(e.model.__name__, e.errors()) from e  # type: ignore

            # Update state with validated_data
            current_state.update(form_validated_data.dict())

            # Make next form
            generated_form = generator.send(form_validated_data)
        else:
            # Form is not completely filled raise next form
            raise FormNotCompleteError(generated_form.schema())
    except StopIteration as e:
        # Form is completely filled so we can return the last of the data and
        return e.value

#
# def start_form(
#     form_key: str,
#     user_inputs: list[State] | None = None,
#     user: str = "Just a user",  # Todo: check if we need users inside form logic?
# ) -> State:
#     """Start a process for workflow.
#
#     Args:
#         form_key: name of workflow
#         user_inputs: List of form inputs from frontend
#         user: User who starts this process
#
#     Returns:
#         The data that the user entered into the form
#
#     """
#     if not user_inputs or user_inputs == [{}]:
#         # Ensure the first FormNotComplete is raised from Swagger and when a POST is done without user_inputs:
#         user_inputs = []
#
#     form = get_form(form_key)
#
#     if not form:
#         raise_status(HTTPStatus.NOT_FOUND, "Form does not exist")
#
#     # Todo: decide what we want for initial input
#     initial_state = {
#         "form_key": form_key,
#     }
#
#     try:
#         state = post_form(form, initial_state, user_inputs)
#     except FormValidationError:
#         logger.exception("Validation errors", user_inputs=user_inputs)
#         raise
#
#     return state


class DisplayOnlyFieldType:
    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.nothing

    def nothing(cls, v: Any, field: ModelField) -> Any:
        return field.default


class FormPage(BaseModel):
    class Config:
        json_loads = json_loads
        json_dumps = json_dumps
        title = "unknown"
        extra = Extra.forbid
        validate_all = True

    def __init_subclass__(cls, /, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)  # type:ignore

        # The default and requiredness of a field is not a property of a field
        # In the case of DisplayOnlyFieldTypes, we do kind of want that.
        # Using this method we set the right properties after the form is created
        for field in cls.__fields__.values():
            try:
                if issubclass(field.type_, DisplayOnlyFieldType):
                    field.required = False
                    field.allow_none = True
            except TypeError:
                pass


def ReadOnlyField(
    default: Any = Undefined,
    *,
    const: Optional[bool] = None,
    **extra: Any,
) -> Any:
    return Field(default, const=True, uniforms={"disabled": True, "value": default}, **extra)
