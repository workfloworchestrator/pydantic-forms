from uuid import UUID

import pytest
from pydantic import ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.types import strEnum
from pydantic_forms.validators import ReadOnlyField


class TestEnum(strEnum):
    One = "One"
    Two = "Two"


test_uuid1 = UUID("866525c8-a868-49bc-b006-1a60e492631e")
test_uuid2 = UUID("999925c8-a868-49bc-b006-1a60e4929999")


@pytest.mark.parametrize(
    "python_value,json_value,json_type,other_python_value,",
    [
        (1, 1, "integer", 123),
        (test_uuid1, str(test_uuid1), "string", test_uuid2),
        (TestEnum.Two, str(TestEnum.Two), "string", TestEnum.One),
    ],
)
def test_read_only_field(python_value, json_value, json_type, other_python_value):
    class Form(FormPage):
        read_only: ReadOnlyField(python_value)

    expected = {
        "title": "unknown",
        "type": "object",
        "properties": {
            "read_only": {
                "const": json_value,
                "default": json_value,
                "title": "Read Only",
                "uniforms": {"disabled": True, "value": json_value},
                "type": json_type,
            }
        },
        "additionalProperties": False,
    }

    assert Form.model_json_schema() == expected

    validated = Form(read_only=python_value)
    assert validated.read_only == python_value
    assert validated.model_dump() == {"read_only": python_value}
    assert validated.model_dump_json() == '{"read_only":"%s"}' % (json_value,)

    with pytest.raises(ValidationError, match=r"read_only\n\s+Input should be"):
        Form(read_only=other_python_value)


@pytest.mark.parametrize("value", [test_uuid1, TestEnum.One])
def test_read_only_field_type_conversion(value):
    class Form(FormPage):
        read_only: ReadOnlyField(value)

    assert Form(read_only=value).read_only == value

    # Test that string representations of UUID and Enums are converted to their original type
    assert Form(read_only=str(value)).read_only == value
    assert Form(read_only=str(value)).model_dump() == {"read_only": value}
