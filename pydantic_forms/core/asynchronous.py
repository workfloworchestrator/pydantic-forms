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
from typing import Any, Dict, List, Union
from unittest.mock import MagicMock

import structlog
from pydantic import ValidationError

from pydantic_forms.core.shared import get_form
from pydantic_forms.exceptions import FormException, FormNotCompleteError, FormValidationError
from pydantic_forms.types import InputForm, State, StateInputFormGenerator

logger = structlog.get_logger(__name__)


async def generate_form(
    form_generator: Union[StateInputFormGenerator, None], state: State, user_inputs: List[State]
) -> Union[State, None]:
    """Generate form using form generator as defined by a form definition."""
    try:
        # Generate form is basically post_form
        await post_form(form_generator, state, user_inputs)
    except FormNotCompleteError as e:
        # Form is not finished and raises the next form, this is expected
        return e.form

    # Form is finished and thus there is no new form
    return None


async def post_form(
    form_generator: Union[StateInputFormGenerator, None], state: State, user_inputs: List[State]
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
    generated_form: InputForm = await generator.asend(None)

    # Loop through user inputs and for each input validate and update current state and validation results
    for user_input in user_inputs:
        # Check last item (asyncgenerator can only yield, not return)
        if isinstance(generated_form, dict):
            break

        # Validate
        try:
            form_validated_data = generated_form(**user_input)
        except ValidationError as e:
            raise FormValidationError(e.model.__name__, e.errors()) from e  # type: ignore

        # Update state with validated_data
        current_state.update(form_validated_data.dict())

        # Make next form
        generated_form = await generator.asend(form_validated_data)

    try:
        # Send something into the asyncgenerator.
        await generator.asend(MagicMock())
    except StopAsyncIteration:
        # Form is completely filled so we can return the last of the data
        return generated_form
    else:
        # Form is not completely filled raise next form
        raise FormNotCompleteError(generated_form.schema())


async def start_form(
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
        raise FormException(f"Form {form_key} does not exist.")

    initial_state = dict(form_key=form_key, **extra_state)

    try:
        state = await post_form(form, initial_state, user_inputs)
    except FormValidationError:
        logger.exception("Validation errors", user_inputs=user_inputs)
        raise

    return state