import pytest
from pydantic import ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.validators import ListOfTwo


class Form(FormPage):
    two: ListOfTwo[int]


def test_list_of_two_ok():
    assert Form(two=[1, 2])


def test_list_of_two_min_items():
    with pytest.raises(ValidationError) as error_info:
        assert Form(two=[1])

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "input": [1],
            "loc": ("two",),
            "msg": "Value error, ensure this value has at least 2 items",
            "type": "value_error",
            # "ctx": {"limit_value": 2},
        }
    ]
    assert errors == expected


def test_list_of_two_max_items():
    with pytest.raises(ValidationError) as error_info:
        assert Form(two=[1, 2, 3])

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "input": [1, 2, 3],
            "loc": ("two",),
            "msg": "Value error, ensure this value has at most 2 items",
            "type": "value_error",
            # "ctx": {"limit_value": 2},
        },
    ]
    assert errors == expected


def test_list_of_two_schema():
    class Form(FormPage):
        list: ListOfTwo[str]

    expected = {
        "additionalProperties": False,
        "properties": {
            "list": {
                "items": {"type": "string"},
                "title": "List",
                "minItems": 2,
                "maxItems": 2,
                "type": "array",
            }
        },
        "required": ["list"],
        "title": "unknown",
        "type": "object",
    }
    assert Form.model_json_schema() == expected
