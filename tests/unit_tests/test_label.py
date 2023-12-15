from pydantic_forms.core import FormPage
from pydantic_forms.validators import Label


class Form(FormPage):
    label: Label = "value"


def test_label_with_value():
    assert Form().model_dump() == {"label": "value"}


def test_label_update_not_allowed():
    assert Form(label="fob").model_dump() == {
        "label": "value",
    }
