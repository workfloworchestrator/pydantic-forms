# Copyright 2019-2023 SURF.
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
from inspect import isasyncgenfunction
from typing import Any, Union

import structlog
from pydantic import ValidationError
from pydantic_i18n import PydanticI18n

from pydantic_forms.core.shared import FORMS
from pydantic_forms.core.translations import translations
from pydantic_forms.exceptions import (
    FormException,
    FormNotCompleteError,
    FormOverflowError,
    FormValidationError,
)
from pydantic_forms.types import InputForm, State, StateInputFormGeneratorAsync

logger = structlog.get_logger(__name__)


async def generate_form(
    form_generator: Union[StateInputFormGeneratorAsync, None],
    state: State,
    user_inputs: list[State],
    locale: str = "en_US",
    extra_translations: Union[dict[str, str], None] = None,
) -> Union[State, None]:
    """Generate form using form generator as defined by a form definition."""
    try:
        # Generate form is basically post_form
        await post_form(form_generator, state, user_inputs, locale, extra_translations)
    except FormNotCompleteError as e:
        # Form is not finished and raises the next form, this is expected
        return e.form

    # Form is finished and thus there is no new form
    return None


async def post_form(
    form_generator: Union[StateInputFormGeneratorAsync, None],
    state: State,
    user_inputs: list[State],
    locale: str = "en_US",
    extra_translations: Union[dict[str, str], None] = None,
) -> State:
    """Post user_input based ond serve a new form if the form wizard logic dictates it."""
    # there is no form_generator so we return no validated data
    if not form_generator:
        return {}

    current_state = deepcopy(state)

    logger.debug("Post form", state=state, user_inputs=user_inputs)

    # Initialize generator
    generator = form_generator(current_state)

    # Generate first form (we need to send None here, since the arguments are already given
    # when we initialized the generator)
    generated_form: Union[InputForm, dict] = await generator.asend(None)

    # Loop through user inputs and for each input validate and update current state and validation results
    user_inputs = user_inputs.copy()
    while user_inputs and not isinstance(generated_form, dict):
        user_input = user_inputs.pop(0)

        # Validate
        try:
            form_validated_data = generated_form(**user_input)
        except ValidationError as e:
            # Todo: add extra_translation to tr
            tr = PydanticI18n(translations)
            raise FormValidationError(generated_form.__name__, e, tr, locale) from e

        # Update state with validated_data
        current_state.update(form_validated_data.model_dump())

        # Make next form
        generated_form = await generator.asend(form_validated_data)

    if user_inputs:
        raise FormOverflowError(f"Did not process all user_inputs ({len(user_inputs)} remaining)")

    if isinstance(generated_form, dict):
        # Check whether the result was yielded. (AsyncGenerator can only yield, not return)
        # This is a downside of using AsyncGenerator; we cannot enforce the last returned item
        # to be of `State`
        return generated_form

    # Form is not completely filled raise next form
    raise FormNotCompleteError(generated_form.model_json_schema(), meta=getattr(generated_form, "meta__", None))


def _get_form(key: str) -> StateInputFormGeneratorAsync:
    if not (func := FORMS.get(key)):
        raise FormException(f"Form {key} does not exist.")

    if not isasyncgenfunction(func):
        raise FormException(f"Form {key} is not an asyncgenerator function")

    return func


async def start_form(
    form_key: str,
    user_inputs: Union[list[State], None] = None,
    user: str = "Just a user",  # Todo: check if we need users inside form logic?
    locale: str = "en_US",
    extra_translations: Union[dict[str, str], None] = None,
    **extra_state: Any,
) -> State:
    """Handle the logic for the endpoint that the frontend uses to render a form with or without prefilled input.

    Args:
    ----
        form_key: name of form in the FORM dict
        user_inputs: List of form inputs from frontend
        user: User who starts this form
        locale: Language of the form
        extra_translations: Extra translations to apply to the form
        extra_state: Optional initial state variables

    Returns:
    -------
        The data that the user entered into the form

    """
    if user_inputs is None:
        # Ensure the first FormNotComplete is raised from Swagger when a POST is done without user_inputs:
        user_inputs = []

    form: StateInputFormGeneratorAsync = _get_form(form_key)

    initial_state = dict(form_key=form_key, **extra_state)

    try:
        state = await post_form(form, initial_state, user_inputs, locale, extra_translations)
    except FormValidationError as exc:
        logger.debug("Validation errors", user_inputs=user_inputs, form=exc.validator_name, errors=exc.errors)
        logger.debug(str(exc))
        raise

    return state
