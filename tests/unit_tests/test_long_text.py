from pydantic_forms.core import FormPage
from pydantic_forms.validators import LongText


def test_long_text_schema():
    class Form(FormPage):
        long_text: LongText

    expected = {
        "additionalProperties": False,
        "properties": {"long_text": {"format": "long", "title": "Long Text", "type": "string"}},
        "required": ["long_text"],
        "title": "unknown",
        "type": "object",
    }

    assert Form.model_json_schema() == expected
