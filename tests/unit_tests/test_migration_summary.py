from uuid import uuid4

from pydantic_forms.core import FormPage
from pydantic_forms.validators import DisplaySubscription, Label, migration_summary


def test_display_default():
    some_sub_id = uuid4()

    Summary = migration_summary(data={"headers": ["one"]})

    class Form(FormPage):
        display_sub: DisplaySubscription = some_sub_id
        label: Label = "bla"
        migration_summary: Summary

    assert Form().model_dump() == {
        "display_sub": some_sub_id,
        "label": "bla",
        "migration_summary": None,
    }

    assert Form(display_sub="").model_dump() == {
        "display_sub": some_sub_id,
        "label": "bla",
        "migration_summary": None,
    }


def test_migration_summary_schema():
    Summary = migration_summary(data={"headers": ["one"]})

    class Form(FormPage):
        ms: Summary

    expected = {
        "$defs": {"MigrationSummaryValue": {"properties": {}, "title": "MigrationSummaryValue", "type": "object"}},
        "additionalProperties": False,
        "properties": {
            "ms": {
                "$ref": "#/$defs/MigrationSummaryValue",
                "default": None,
                "format": "summary",
                "type": "string",
                "uniforms": {
                    "data": {"headers": ["one"]},
                },
            },
        },
        "title": "unknown",
        "type": "object",
    }

    assert Form.model_json_schema() == expected
