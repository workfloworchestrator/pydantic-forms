from uuid import uuid4

import pytest

from pydantic_forms.core import FormPage
from pydantic_forms.validators import DisplaySubscription, Label


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


@pytest.mark.skip(reason="Dont bother about schema right now")
def test_display_only_schema():
    some_sub_id = uuid4()

    class Form(FormPage):
        display_sub: DisplaySubscription = some_sub_id
        label: Label
        migration_summary: migration_summary({"headers": ["one"]})  # noqa: F821

    expected = {
        "additionalProperties": False,
        "properties": {
            "display_sub": {
                "default": str(some_sub_id),
                "format": "subscription",
                "title": "Display Sub",
                "type": "string",
            },
            "label": {"format": "label", "title": "Label", "type": "string"},
            "migration_summary": {
                "format": "summary",
                "title": "Migration Summary",
                "type": "string",
                "uniforms": {"data": {"headers": ["one"]}},
            },
        },
        "title": "unknown",
        "type": "object",
    }

    assert Form.model_json_schema() == expected
