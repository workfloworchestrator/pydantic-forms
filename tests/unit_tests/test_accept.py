from pydantic_core import ValidationError
from pytest import raises

from pydantic_forms.core import FormPage
from pydantic_forms.utils.json import json_dumps, json_loads
from pydantic_forms.validators import Accept


def test_accept_ok():
    class Form(FormPage):
        accept: Accept

    validated_data = Form(accept="ACCEPTED").model_dump_json()

    expected = {"accept": True}
    assert json_loads(validated_data) == expected


def test_accept_schema():
    class Form(FormPage):
        accept: Accept

    expected = {
        "additionalProperties": False,
        "properties": {
            "accept": {
                "enum": ["ACCEPTED", "INCOMPLETE"],
                "format": "accept",
                "type": "string",
                "title": "Accept",
            }
        },
        "required": ["accept"],
        "title": "unknown",
        "type": "object",
    }
    assert Form.model_json_schema() == expected


def test_accept_schema_with_data():
    class SpecialAccept(Accept):
        data = [("field", "label")]

    class Form(FormPage):
        accept: SpecialAccept

    expected = {
        "additionalProperties": False,
        "properties": {
            "accept": {
                "data": [("field", "label")],
                "enum": ["ACCEPTED", "INCOMPLETE"],
                "format": "accept",
                "type": "string",
                "title": "Accept",
            }
        },
        "required": ["accept"],
        "title": "unknown",
        "type": "object",
    }
    assert Form.model_json_schema() == expected


def test_accept_nok_incomplete():
    class Form(FormPage):
        accept: Accept

    with raises(ValidationError) as error_info:
        Form(accept="INCOMPLETE")

    expected = [
        {"input": "INCOMPLETE", "loc": ("accept",), "msg": "Value error, Not all tasks are done", "type": "value_error"}
    ]
    assert error_info.value.errors(include_context=False, include_url=False) == expected


def test_accept_nok_invalid():
    class Form(FormPage):
        accept: Accept

    with raises(ValidationError) as error_info:
        Form(accept="Bla")

    expected = [
        {
            "input": "Bla",
            "ctx": {"enum_values": [Accept.Values.ACCEPTED, Accept.Values.INCOMPLETE]},
            "loc": ("accept",),
            "msg": "value is not a valid enumeration member; permitted: 'ACCEPTED', 'INCOMPLETE'",
            "type": "type_error.enum",
        }
    ]
    assert error_info.value.errors() == expected