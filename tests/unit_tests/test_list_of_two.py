import pytest
from pydantic import ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.validators import ListOfTwo


def test_list_of_two():
    class Form(FormPage):
        two: ListOfTwo[int]

    assert Form(two=[1, 2])

    with pytest.raises(ValidationError) as error_info:
        assert Form(two=[1])

    expected = [
        {
            "ctx": {"limit_value": 2},
            "loc": ("two",),
            "msg": "ensure this value has at least 2 items",
            "type": "value_error.list.min_items",
        }
    ]
    assert expected == error_info.value.errors()

    with pytest.raises(ValidationError) as error_info:
        assert Form(two=[1, 2, 3])

    expected = [
        {
            "ctx": {"limit_value": 2},
            "loc": ("two",),
            "msg": "ensure this value has at most 2 items",
            "type": "value_error.list.max_items",
        },
    ]
    assert expected == error_info.value.errors()


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
    assert expected == Form.schema()
