from pydantic_forms.core import FormPage
from pydantic_forms.validators import Hidden


class Form(FormPage):
    hidden: Hidden = "hidden value"


def test_hidden_with_value():
    assert Form().model_dump() == {"hidden": "hidden value"}


def test_hidden_update_not_allowed():
    assert Form(hidden="fob").model_dump() == {
        "hidden": "hidden value",
    }
