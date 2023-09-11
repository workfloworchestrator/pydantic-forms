from uuid import uuid4

from pydantic_forms.core import FormPage
from pydantic_forms.validators import DisplaySubscription, Label, migration_summary


def test_display():
    class Form(FormPage):
        display_sub: DisplaySubscription
        label: Label
        migration_summary: migration_summary({"headers": ["one"]})  # noqa: F821

    assert Form().dict() == {"display_sub": None, "label": None, "migration_summary": None}
    assert Form(display_sub="foo", label="bar", migration_summary="baz").dict() == {
        "display_sub": None,
        "label": None,
        "migration_summary": None,
    }


def test_display_only_schema():
    some_sub_id = uuid4()

    class Form(FormPage):
        display_sub: DisplaySubscription = some_sub_id
        label: Label
        migration_summary: migration_summary({"headers": ["one"]})  # noqa: F821

    assert Form.schema() == {
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
