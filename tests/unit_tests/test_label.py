from pydantic_forms.core import FormPage
from pydantic_forms.validators import Divider, Label


def test_labels_with_value_and_dividers():
    class Form(FormPage):
        label: Label = "value"
        # divider: Divider

    assert Form().model_dump() == {"label": "value", "divider": None}
    #
    # assert Form(label="fob", divider="baz").model_dump() == {
    #     "label": "value",
    #     "divider": None,
    # }
