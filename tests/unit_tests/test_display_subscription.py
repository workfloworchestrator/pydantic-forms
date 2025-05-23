from uuid import uuid4

from pydantic_forms.core import FormPage
from pydantic_forms.validators import DisplaySubscription, Label, migration_summary
from tests.unit_tests.helpers import PYDANTIC_VERSION


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


def test_display_only_schema():
    some_sub_id = uuid4()
    Summary = migration_summary({"headers": ["one"]})

    class Form(FormPage):
        display_sub: DisplaySubscription = some_sub_id
        label: Label
        summary: Summary

    if PYDANTIC_VERSION == "2.8":
        summary_ref = {"allOf": [{"$ref": "#/$defs/MigrationSummaryValue"}]}
    else:
        summary_ref = {"$ref": "#/$defs/MigrationSummaryValue"}

    expected = {
        "$defs": {"MigrationSummaryValue": {"properties": {}, "title": "MigrationSummaryValue", "type": "object"}},
        "additionalProperties": False,
        "properties": {
            "display_sub": {
                "default": str(some_sub_id),
                "format": "subscription",
                "title": "Display Sub",
                "type": "string",
            },
            "label": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "format": "label",
                "default": None,
                "title": "Label",
                "type": "string",
            },
            "summary": {
                **summary_ref,
                "default": None,
                "format": "summary",
                "type": "string",
                "uniforms": {"data": {"headers": ["one"]}},
            },
        },
        "title": "unknown",
        "type": "object",
    }

    assert Form.model_json_schema() == expected
