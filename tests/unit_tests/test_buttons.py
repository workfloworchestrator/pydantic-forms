from typing import ClassVar

import pytest

from pydantic_forms.core import FormPage, post_form
from pydantic_forms.exceptions import FormNotCompleteError
from pydantic_forms.types import FormMeta
from pydantic_forms.validators import Button, ButtonsConfig

CONFIRM = ButtonsConfig(next=Button(text="Confirm", color="danger"))
CONFIRM_META = {"next": {"text": "Confirm", "color": "danger"}}


class HasNextPage(FormPage):
    meta__: ClassVar[FormMeta | None] = {"hasNext": False}


class CustomButtonsPage(FormPage):
    meta__: ClassVar[FormMeta | None] = {"customButtons": {"previous": {"text": "Back"}}}


def test_buttons_field_is_display_only():
    class Form(FormPage):
        custom_buttons: ButtonsConfig = CONFIRM
        name: str

    assert "custom_buttons" not in Form.model_json_schema()["properties"]
    assert Form(name="foo", custom_buttons="bar").model_dump() == {"custom_buttons": None, "name": "foo"}


@pytest.mark.parametrize(
    "base,expected",
    [
        pytest.param(FormPage, {"customButtons": CONFIRM_META}, id="no-meta"),
        pytest.param(HasNextPage, {"hasNext": False, "customButtons": CONFIRM_META}, id="with-meta"),
    ],
)
def test_buttons_sent_as_meta(base, expected):
    class Form(base):
        custom_buttons: ButtonsConfig = CONFIRM

    def form(state):
        yield Form
        return {}

    with pytest.raises(FormNotCompleteError) as error_info:
        post_form(form, {}, [])

    assert error_info.value.meta == expected
    assert Form.meta__ == base.meta__


def test_buttons_field_conflicts_with_meta_custom_buttons():
    with pytest.raises(TypeError, match="Form declares its buttons both in meta__"):

        class Form(CustomButtonsPage):
            custom_buttons: ButtonsConfig = CONFIRM


def test_more_than_one_buttons_field_conflicts():
    with pytest.raises(TypeError, match="Form has more than one ButtonsConfig field"):

        class Form(FormPage):
            custom_buttons: ButtonsConfig = CONFIRM
            other_buttons: ButtonsConfig = CONFIRM


def test_buttons_field_needs_default():
    with pytest.raises(TypeError, match="Form.custom_buttons needs a ButtonsConfig"):

        class Form(FormPage):
            custom_buttons: ButtonsConfig
