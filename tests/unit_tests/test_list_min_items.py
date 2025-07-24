from typing import Annotated

import pytest
from pydantic import ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.validators import MinItems


@pytest.fixture(name="Form")
def form_with_list_with_min_one_item():
    class _Form(FormPage):
        min_one: Annotated[
            list[int],
            MinItems(1)
        ]

    return _Form


def test_list_list_with_min_one_item_ok(Form):
    assert Form(min_one=[1])

def test_list_list_with_min_one_item_less_nok(Form):
    with pytest.raises(ValidationError) as error_info:
        assert Form(min_one=[])

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "input": [],
            "loc": ("min_one",),
            "msg": "List should have at least 1 item after validation, not 0",
            "type": "too_short",
        },
    ]
    assert errors == expected

