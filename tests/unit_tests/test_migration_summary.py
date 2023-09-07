from uuid import uuid4

from pydantic_forms.core import FormPage
from pydantic_forms.validators import MigrationSummary, DisplaySubscription, Label, migration_summary


def test_display_default():
    some_sub_id = uuid4()

    class Summary(MigrationSummary):
        data = {"headers": ["one"]}

    class Form(FormPage):
        display_sub: DisplaySubscription = some_sub_id
        label: Label = "bla"
        migration_summary: Summary = "foo"

    assert Form().dict() == {
        "display_sub": some_sub_id,
        "label": "bla",
        "migration_summary": "foo",
    }
    assert Form(display_sub="").dict() == {
        "display_sub": some_sub_id,
        "label": "bla",
        "migration_summary": "foo",
    }


def test_migration_summary_schema():
    class Summary(MigrationSummary):
        data = "foo"

    class Form(FormPage):
        ms1: Summary
        ms2: migration_summary("bar")  # noqa: F821

    assert Form.schema() == {
        "additionalProperties": False,
        "properties": {
            "ms1": {"format": "summary", "title": "Ms1", "type": "string", "uniforms": {"data": "foo"}},
            "ms2": {"format": "summary", "title": "Ms2", "type": "string", "uniforms": {"data": "bar"}},
        },
        "title": "unknown",
        "type": "object",
    }
