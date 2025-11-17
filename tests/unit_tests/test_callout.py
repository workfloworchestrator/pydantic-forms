from uuid import uuid4

from pydantic_forms.core import FormPage
from pydantic_forms.validators import DisplaySubscription, Label
from pydantic_forms.validators.components.callout import CalloutMessageType, callout
from tests.unit_tests.helpers import PYDANTIC_VERSION


def test_callout_default():
    """Ensure Callout default is None and schema defaults are correctly injected."""
    CalloutField = callout(
        header="Test header",
        message="This is a test message",
        icon_type="info",
        message_type=CalloutMessageType.SUCCESS,
    )

    some_sub_id = uuid4()

    class Form(FormPage):
        display_sub: DisplaySubscription = some_sub_id
        label: Label = "bla"
        callout_field: CalloutField

    # The field itself should default to None (display-only)
    assert Form().model_dump() == {
        "display_sub": some_sub_id,
        "label": "bla",
        "callout_field": None,
    }

    # And the field accepts no input (display only)
    assert Form(display_sub="").model_dump() == {
        "display_sub": some_sub_id,
        "label": "bla",
        "callout_field": None,
    }


def test_callout_schema():
    """Ensure the callout field generates a correct JSON schema with default data."""
    CalloutField = callout(
        header="Header",
        message="A message",
        icon_type="bell",
        message_type="danger",
    )

    class Form(FormPage):
        callout_field: CalloutField

    if PYDANTIC_VERSION == "2.8":
        callout_field_ref = {"allOf": [{"$ref": "#/$defs/CalloutValue"}]}
    else:
        callout_field_ref = {"$ref": "#/$defs/CalloutValue"}

    expected = {
        "$defs": {"CalloutValue": {"properties": {}, "title": "CalloutValue", "type": "object"}},
        "additionalProperties": False,
        "properties": {
            "callout_field": {
                **callout_field_ref,
                "default": {
                    "header": "Header",
                    "message": "A message",
                    "icon_type": "bell",
                    "message_type": "danger",
                },
                "format": "callout",
                "type": "string",
            },
        },
        "title": "unknown",
        "type": "object",
    }

    assert Form.model_json_schema() == expected


def test_callout_accepts_custom_message_type():
    """Ensure custom (non-enum) message_type values are accepted and serialized correctly."""
    CalloutField = callout(
        header="Custom",
        message="Supports custom color values",
        icon_type="iInCircle",
        message_type="neutral",  # custom
    )

    class Form(FormPage):
        callout_field: CalloutField

    schema = Form.model_json_schema()

    default_data = schema["properties"]["callout_field"]["default"]
    assert default_data["message_type"] == "neutral"
    assert default_data["header"] == "Custom"
    assert default_data["icon_type"] == "iInCircle"
