import pytest

from pydantic_forms.core import FormPage, ReadOnlyField


def test_read_only_field_schema():
    class Form(FormPage):
        read_only: int = ReadOnlyField(1, const=False)

    expected = {
        "title": "unknown",
        "type": "object",
        "properties": {
            "read_only": {
                "default": 1,
                "title": "Read Only",
                "uniforms": {"disabled": True, "value": 1},
                "type": "integer",
            }
        },
        "additionalProperties": False,
    }

    assert Form.model_json_schema() == expected
