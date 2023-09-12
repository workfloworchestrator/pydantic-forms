from pydantic_forms.core import FormPage
from pydantic_forms.validators import Divider


class Form(FormPage):
    divider: Divider


def test_divider_with_value():
    assert Form().model_dump() == {"divider": None}


def test_divider_update_not_allowed():
    assert Form(divider="baz").model_dump() == {
        "divider": None,
    }
