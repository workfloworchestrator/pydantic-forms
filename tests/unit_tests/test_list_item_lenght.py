from typing import Annotated

import pytest
from pydantic import ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.validators import MinItems, ItemLength


@pytest.fixture(name="Form")
def form_with_list_with_min_one_item():
    class _Form(FormPage):
        items: Annotated[
            list[int],
            ItemLength(2,3)
        ]

    return _Form


def test_list_with_one_item_ok(Form):
    assert Form(items=[1,2])

def test_list_with_more_items_nok(Form):
    with pytest.raises(ValidationError) as error_info:
        assert Form(items=[1,2,3,4])

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "input": [1,2,3,4],
            "loc": ("items",),
            "msg": "List should have at most 3 items after validation, not 4",
            "type": "too_long",
        },
    ]
    assert errors == expected

def test_list_with_less_items_nok(Form):
    with pytest.raises(ValidationError) as error_info:
        assert Form(items=[1])

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            'input': [1],
            'loc': ('items',),
            'msg': 'List should have at least 2 items after validation, not 1',
            'type': 'too_short'
        }
    ]
    assert errors == expected


