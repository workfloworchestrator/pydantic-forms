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
from typing import Any, Callable, Dict, Generator, List, Optional, Union

import structlog
from pydantic.config import Extra
from pydantic.error_wrappers import ValidationError
from pydantic.fields import Field, ModelField, Undefined
from pydantic.main import BaseModel

from pydantic_forms.exceptions import FormNotCompleteError, FormValidationError
from pydantic_forms.types import InputForm, State, StateInputFormGenerator
from pydantic_forms.utils.json import json_dumps, json_loads

logger = structlog.get_logger(__name__)


def generate_form(
    form_generator: Union[StateInputFormGenerator, None], state: State, user_inputs: List[State]
) -> Union[State, None]:
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
    """Post user_input based ond serve a new form if the form wizard logic dictates it."""
    # there is no form_generator so we return no validated data
    if not form_generator:
        return {}

    current_state = deepcopy(state)

    logger.debug("Post form", state=state, user_inputs=user_inputs)

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


def start_form(
    form_key: str,
    user_inputs: Union[List[State], None] = None,
    user: str = "Just a user",  # Todo: check if we need users inside form logic?
    **extra_state: Dict[str, Any],
) -> State:
    """Handle the logic for the endpoint that the frontend uses to render a form with or without prefilled input.

    Args:
        form_key: name of form in the FORM dict
        user_inputs: List of form inputs from frontend
        user: User who starts this form
        extra_state: Optional initial state variables

    Returns:
        The data that the user entered into the form

    """
    if user_inputs is None:
        # Ensure the first FormNotComplete is raised from Swagger when a POST is done without user_inputs:
        user_inputs = []

    form = get_form(form_key)

    if not form:
        # raise_status(HTTPStatus.NOT_FOUND, "Form does not exist")
        raise Exception(f"Form {form_key} does not exist.")  # TODO decide on exception to raise for this

    initial_state = dict(form_key=form_key, **extra_state)

    try:
        state = post_form(form, initial_state, user_inputs)
    except FormValidationError:
        logger.exception("Validation errors", user_inputs=user_inputs)
        raise

    return state


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
        super().__init_subclass__(**kwargs)

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
    return Field(default, const=True, uniforms={"disabled": True, "value": default}, **extra)  # type: ignore


FORMS: Dict[str, Callable] = {}


def get_form(key: str) -> Union[Callable, None]:
    return FORMS.get(key)


def register_form(key: str, form: Callable) -> None:
    logger.info("Current Forms", forms=FORMS, new_key=key)
    if key in FORMS and form is not FORMS[key]:
        raise Exception(f"Trying to re-register form {key} with a different function")
    FORMS[key] = form


def list_forms() -> List[str]:
    return list(FORMS.keys())
