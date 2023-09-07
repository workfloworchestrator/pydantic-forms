import pytest

from pydantic_forms.core import FormPage, ReadOnlyField


@pytest.mark.xfail(reason="fix flakey test")
def test_read_only_field_schema():
    class Form(FormPage):
        read_only: int = ReadOnlyField(1, const=False)

    assert Form.schema() == {
        "title": "unknown",
        "type": "object",
        "properties": {
            "read_only": {
                "title": "Read Only",
                "const": 1,
                "uniforms": {"disabled": True, "value": 1},
                "type": "integer",
            }
        },
        "additionalProperties": False,
    }
