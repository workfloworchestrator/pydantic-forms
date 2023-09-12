from uuid import uuid4

from pydantic_forms.core import FormPage
from pydantic_forms.validators import DisplaySubscription


def test_display_subscription():
    some_sub_id = uuid4()

    class Form(FormPage):
        display_sub: DisplaySubscription = some_sub_id

    expected = {"display_sub": some_sub_id}

    assert Form().model_dump() == expected


def test_display_subscription_update_not_allowed():
    some_sub_id = uuid4()

    class Form(FormPage):
        display_sub: DisplaySubscription = some_sub_id

    expected = {"display_sub": some_sub_id}

    assert Form(display_sub=uuid4()).model_dump() == expected
