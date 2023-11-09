import pytest
from pydantic import ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.validators import ListOfOne


@pytest.fixture(name="Form")
def form_with_list_of_one():
    class _Form(FormPage):
        one: ListOfOne[int]

    return _Form


def test_list_of_one_ok(Form):
    assert Form(one=[1])


def test_list_of_one_min_items(Form):
    with pytest.raises(ValidationError) as error_info:
        assert Form(one=[])

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "input": [],
            "loc": ("one",),
            "msg": "List should have at least 1 item after validation, not 0",
            "type": "too_short",
        }
    ]
    assert errors == expected


def test_list_of_one_max_items(Form):
    with pytest.raises(ValidationError) as error_info:
        assert Form(one=[1, 2])

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "input": [1, 2],
            "loc": ("one",),
            "msg": "List should have at most 1 item after validation, not 2",
            "type": "too_long",
        },
    ]
    assert errors == expected
