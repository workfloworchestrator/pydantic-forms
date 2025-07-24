from typing import Annotated

import pytest
from pydantic import ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.validators import MaxItems


@pytest.fixture(name="Form")
def form_with_list_with_max_one_item():
    class _Form(FormPage):
        max_one: Annotated[
            list[int],
            MaxItems(1)
        ]

    return _Form


def test_list_list_with_max_one_item_ok(Form):
    assert Form(max_one=[1])

def test_list_list_with_max_one_item_more_nok(Form):
    with pytest.raises(ValidationError) as error_info:
        assert Form(max_one=[1,2])

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "input": [1, 2],
            "loc": ("max_one",),
            "msg": "List should have at most 1 item after validation, not 2",
            "type": "too_long",
        },
    ]
    assert errors == expected

