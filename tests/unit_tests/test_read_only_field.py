import json
from uuid import UUID

from more_itertools import first
from pydantic.config import JsonDict
import pytest
from pydantic import BaseModel, ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.types import strEnum
from pydantic_forms.validators import read_only_field, read_only_list, LongText, OrganisationId
from pydantic_forms.validators.components.read_only import merge_json_schema, _get_field_info_with_schema


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
        read_only: read_only_field(read_only_value)

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
        (["a", "b"], str, ["a", "b"], {"type": "string"}),
        ([1, 2], int, [1, 2], {"type": "integer"}),
        ([test_uuid1], UUID, [str(test_uuid1)], {"format": "uuid", "type": "string"}),
    ],
)
def test_read_only_field_list_schema(read_only_value, read_only_type, schema_value, expected_item_type):
    class Form(FormPage):
        read_only_list: read_only_list(read_only_value)

    expected = {
        "title": "unknown",
        "type": "object",
        "properties": {
            "read_only_list": {
                "default": schema_value,
                "items": expected_item_type,
                "title": "Read Only List",
                "uniforms": {"disabled": True, "value": schema_value},
                "type": "array",
            }
        },
        "additionalProperties": False,
    }

    assert Form.model_json_schema() == expected

    validated = Form(read_only_list=read_only_value)
    assert validated.read_only_list == read_only_value
    assert validated.model_dump() == {"read_only_list": read_only_value}
    assert validated.model_dump_json() == json.dumps({"read_only_list": schema_value}, separators=(",", ":"))


@pytest.mark.parametrize(
    "wrong_value",
    (None, [], ["a"], ["a", "bb"], ["b", "a"], ["a", "a", "b"]),
)
def test_read_only_field_list_validation_string(wrong_value):
    class Form(FormPage):
        read_only: read_only_list(["a", "b"])

    with pytest.raises(ValidationError):
        Form(read_only=wrong_value)


def test_read_only_field_list_with_empty_default_raises_error():
    with pytest.raises(ValueError, match="Default list object must not be empty"):

        class Form(FormPage):
            read_only: read_only_list([])


def test_read_only_field_list_with_mixed_types_raises_error():
    with pytest.raises(TypeError, match="All items in read_only_list must be of same type"):

        class Form(FormPage):
            read_only: read_only_list(["towel", 42])


def test_read_only_field_list_with_None_item_raises_error():
    with pytest.raises(TypeError, match="read_only_list item type cannot be 'NoneType'"):

        class Form(FormPage):
            read_only: read_only_list([None, None])


class Model(BaseModel):
    value: int


def test_read_only_list_model():
    read_only_value = [Model(value=1)]
    schema_value = [model.model_dump() for model in read_only_value]
    expected_item_type = {"$ref": "#/$defs/Model"}

    class Form(FormPage):
        read_only_list: read_only_list(read_only_value)

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
            "read_only_list": {
                "default": schema_value,
                "items": expected_item_type,
                "title": "Read Only List",
                "uniforms": {"disabled": True, "value": schema_value},
                "type": "array",
            }
        },
        "additionalProperties": False,
    }

    assert Form.model_json_schema() == expected

    validated = Form(read_only_list=read_only_value)
    assert validated.read_only_list == read_only_value
    assert validated.model_dump() == {"read_only_list": schema_value}
    assert validated.model_dump_json() == json.dumps({"read_only_list": schema_value}, separators=(",", ":"))

    with pytest.raises(ValidationError, match="Cannot change values for a readonly list"):
        Form(read_only_list=[Model(value=2)])


@pytest.mark.parametrize("value", [test_uuid1, TestEnum.One])
def test_read_only_field_type_conversion(value):
    class Form(FormPage):
        read_only: read_only_field(value)

    assert Form(read_only=value).read_only == value

    # Test that string representations of UUID and Enums are converted to their original type
    assert Form(read_only=str(value)).read_only == value
    assert Form(read_only=str(value)).model_dump() == {"read_only": value}


def test_read_only_field_raises_error_with_list_type():
    with pytest.raises(TypeError, match="Use read_only_list"):

        class Form(FormPage):
            read_only: read_only_field(["nope"])


def test_read_only_field_merge_json_schema():
    long_text = "Some\nLong\nText\n"

    class LongTextForm(FormPage):
        read_only: read_only_field(long_text, LongText)

    long_text_validated = LongTextForm(read_only=long_text)
    long_text_read_only = long_text_validated.model_json_schema()["properties"]["read_only"]
    assert long_text_read_only["format"] == "long"
    assert long_text_read_only["uniforms"]["disabled"]

    class OrgIdForm(FormPage):
        read_only: read_only_field(test_uuid1, OrganisationId)

    org_id_validated = OrgIdForm(read_only=test_uuid1)
    org_id_read_only = org_id_validated.model_json_schema()["properties"]["read_only"]
    assert org_id_read_only["format"] == "organisationId"
    assert org_id_read_only["uniforms"]["disabled"]


def test_read_only_unsupported_type():
    with pytest.raises(TypeError, match="^Cannot make a read_only_field for type"):

        class Form(FormPage):
            read_only: read_only_field({"value": 42})


def test_read_only_merge_json_schema_fails_without_json_schema_extra():
    with pytest.raises(TypeError, match="Target type has no json_schema_extra"):

        class Form(FormPage):
            read_only: read_only_field(True, merge_type=JsonDict)


def test_merge_json_schema():
    with pytest.raises(TypeError, match="Source type has no json_schema_extra"):
        merge_json_schema("text", LongText)

    with pytest.raises(TypeError, match="Target type has no json_schema_extra"):
        merge_json_schema(OrganisationId, test_uuid1)

    # TODO: This may be a test for a contrived error -- not sure if it's possible to hit the block
    # this is testing without messing things up pretty bad as shown here
    with pytest.raises(TypeError, match="^Cannot merge.*"):
        longtext = LongText
        org_id = OrganisationId
        for typ in (longtext, org_id):
            field_info = first(_get_field_info_with_schema(typ))
            field_info.json_schema_extra = "wrong"
        merge_json_schema(org_id, longtext)
