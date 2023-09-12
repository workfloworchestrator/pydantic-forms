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

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            # "ctx": {"limit_value": 1},
            "input": [],
            "loc": ("one",),
            "msg": "Value error, ensure this value has at least 1 items",
            "type": "value_error",
            # "ctx": {"error": ListMinLengthError(limit_value=1)},
        }
    ]
    assert errors == expected


def test_list_of_one_max_items():
    with pytest.raises(ValidationError) as error_info:
        assert Form(one=[1, 2])

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "input": [1, 2],
            "loc": ("one",),
            "msg": "Value error, ensure this value has at most 1 items",
            "type": "value_error",
            # "ctx": {"error": ListMinLengthError(limit_value=1)},
        },
    ]
    assert errors == expected
