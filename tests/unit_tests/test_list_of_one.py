import pytest
from pydantic import ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.validators import ListOfOne


class Form(FormPage):
    one: ListOfOne[int]


def test_list_of_one_ok():
    assert Form(one=[1])


def test_list_of_one_min_items():
    with pytest.raises(ValidationError) as error_info:
        assert Form(one=[])

    expected = [
        {
            "ctx": {"limit_value": 1},
            "loc": ("one",),
            "msg": "ensure this value has at least 1 items",
            "type": "value_error.list.min_items",
        }
    ]
    assert error_info.value.errors() == expected


def test_list_of_one_max_items():
    with pytest.raises(ValidationError) as error_info:
        assert Form(one=[1, 2])

    expected = [
        {
            "ctx": {"limit_value": 1},
            "loc": ("one",),
            "msg": "ensure this value has at most 1 items",
            "type": "value_error.list.max_items",
        },
    ]
    assert error_info.value.errors() == expected
