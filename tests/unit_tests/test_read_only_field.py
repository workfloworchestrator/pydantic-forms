import json
from uuid import UUID

import pytest
from pydantic import BaseModel, ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.types import strEnum
from pydantic_forms.validators import ReadOnlyField


class TestEnum(strEnum):
    One = "One"
    Two = "Two"


test_uuid1 = UUID("866525c8-a868-49bc-b006-1a60e492631e")
test_uuid2 = UUID("999925c8-a868-49bc-b006-1a60e4929999")


@pytest.mark.parametrize(
    "read_only_value,schema_value,schema_type,other_python_value",
    [
        (1, 1, "integer", 123),
        (test_uuid1, str(test_uuid1), "string", test_uuid2),
        (TestEnum.Two, str(TestEnum.Two), "string", TestEnum.One),
        (None, None, "string", "foo"),
    ],
)
def test_read_only_field_schema(read_only_value, schema_value, schema_type, other_python_value):
    class Form(FormPage):
        read_only: ReadOnlyField(read_only_value, default_type=None)

    expected = {
        "title": "unknown",
        "type": "object",
        "properties": {
            "read_only": {
                "const": schema_value,
                "default": schema_value,
                "title": "Read Only",
                "uniforms": {"disabled": True, "value": schema_value},
                "type": schema_type,
            }
        },
        "additionalProperties": False,
    }

    assert Form.model_json_schema() == expected

    validated = Form(read_only=read_only_value)
    assert validated.read_only == read_only_value
    assert validated.model_dump() == {"read_only": read_only_value}
    assert validated.model_dump_json() == '{"read_only":"%s"}' % (schema_value,)

    with pytest.raises(ValidationError, match=r"read_only\n\s+Input should be"):
        Form(read_only=other_python_value)


@pytest.mark.parametrize(
    "read_only_value,read_only_type,schema_value,expected_item_type",
    [
        (["a", "b"], list[str], ["a", "b"], {"type": "string"}),
        ([1, 2], list[int], [1, 2], {"type": "integer"}),
        ([test_uuid1], list[UUID], [str(test_uuid1)], {"format": "uuid", "type": "string"}),
    ],
)
def test_read_only_field_list_schema(read_only_value, read_only_type, schema_value, expected_item_type):
    class Form(FormPage):
        read_only: ReadOnlyField(read_only_value, default_type=read_only_type)

    expected = {
        "title": "unknown",
        "type": "object",
        "properties": {
            "read_only": {
                "const": schema_value,
                "default": schema_value,
                "items": expected_item_type,
                "title": "Read Only",
                "uniforms": {"disabled": True, "value": schema_value},
                "type": "array",
            }
        },
        "additionalProperties": False,
    }

    assert Form.model_json_schema() == expected

    validated = Form(read_only=read_only_value)
    assert validated.read_only == read_only_value
    assert validated.model_dump() == {"read_only": read_only_value}
    assert validated.model_dump_json() == json.dumps({"read_only": schema_value}, separators=(",", ":"))


@pytest.mark.parametrize(
    "wrong_value",
    (None, [], ["a"], ["a", "bb"], ["b", "a"], ["a", "a", "b"]),
)
def test_read_only_field_list_validation_string(wrong_value):
    class Form(FormPage):
        read_only: ReadOnlyField(["a", "b"], default_type=list[str])

    with pytest.raises(ValidationError):
        Form(read_only=wrong_value)


def test_read_only_field_list_without_type_raises_error():
    with pytest.raises(TypeError, match="Need the default_type parameter"):

        class Form(FormPage):
            read_only: ReadOnlyField(["a", "b"])


class Model(BaseModel):
    value: int


def test_read_only_field_list_model():
    read_only_value = [Model(value=1)]
    schema_value = [model.model_dump() for model in read_only_value]
    expected_item_type = {"$ref": "#/$defs/Model"}

    class Form(FormPage):
        read_only: ReadOnlyField(read_only_value, default_type=list[Model])

    expected = {
        "$defs": {
            "Model": {
                "properties": {"value": {"title": "Value", "type": "integer"}},
                "required": ["value"],
                "title": "Model",
                "type": "object",
            }
        },
        "title": "unknown",
        "type": "object",
        "properties": {
            "read_only": {
                "const": schema_value,
                "default": schema_value,
                "items": expected_item_type,
                "title": "Read Only",
                "uniforms": {"disabled": True, "value": schema_value},
                "type": "array",
            }
        },
        "additionalProperties": False,
    }

    assert Form.model_json_schema() == expected

    validated = Form(read_only=read_only_value)
    assert validated.read_only == read_only_value
    assert validated.model_dump() == {"read_only": schema_value}
    assert validated.model_dump_json() == json.dumps({"read_only": schema_value}, separators=(",", ":"))

    with pytest.raises(ValidationError, match="Cannot change values for a readonly list"):
        Form(read_only=[Model(value=2)])


@pytest.mark.parametrize("value", [test_uuid1, TestEnum.One])
def test_read_only_field_type_conversion(value):
    class Form(FormPage):
        read_only: ReadOnlyField(value)

    assert Form(read_only=value).read_only == value

    # Test that string representations of UUID and Enums are converted to their original type
    assert Form(read_only=str(value)).read_only == value
    assert Form(read_only=str(value)).model_dump() == {"read_only": value}
