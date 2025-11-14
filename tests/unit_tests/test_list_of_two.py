import pytest
from pydantic import ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.validators import ListOfTwo


@pytest.fixture(name="Form")
def form_with_list_of_two():
    class _Form(FormPage):
        two: ListOfTwo[int]

    return _Form


def test_list_of_two_ok(Form):
    assert Form(two=[1, 2])


def test_list_of_two_min_items(Form):
    with pytest.raises(ValidationError) as error_info:
        assert Form(two=[1])

    errors = error_info.value.errors(include_url=False, include_context=False)

    expected = [
        {
            "input": [1],
            "loc": ("two",),
            "msg": "Value should have at least 2 items after validation, not 1",
            "type": "too_short",
        }
    ]
    assert errors == expected


def test_list_of_two_max_items(Form):
    with pytest.raises(ValidationError) as error_info:
        assert Form(two=[1, 2, 3])

    errors = error_info.value.errors(include_url=False, include_context=False)

    expected = [
        {
            "input": [1, 2, 3],
            "loc": ("two",),
            "msg": "Value should have at most 2 items after validation, not 3",
            "type": "too_long",
        },
    ]
    assert errors == expected


def test_list_of_two_duplicates(Form):
    with pytest.raises(ValidationError) as error_info:
        assert Form(two=[2, 2])

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "type": "unique_list",
            "loc": ("two",),
            "msg": "List must be unique",
            "input": [2, 2],
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
                "uniqueItems": True,
            }
        },
        "required": ["list"],
        "title": "unknown",
        "type": "object",
    }
    assert Form.model_json_schema() == expected
