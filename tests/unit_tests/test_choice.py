from pydantic_core import ValidationError
from pytest import raises

from pydantic_forms.core import FormPage
from pydantic_forms.validators import Choice


def test_choice():
    class LegChoice(Choice):
        Primary = "Primary"
        Secondary = "Secondary"

    class Form(FormPage):
        choice: LegChoice

    # Make sure label classvar is not included
    assert len(LegChoice.__members__) == 2

    # Should still count as string and enum
    assert Form(choice="Primary").choice == "Primary"
    assert Form(choice="Primary").choice == LegChoice.Primary

    # Validation works
    Form(choice="Primary")

    with raises(ValidationError):
        Form(choice="Wrong")


def test_choice_default():
    class LegChoice(Choice):
        Primary = "Primary"
        Secondary = "Secondary"

    class Form(FormPage):
        choice: LegChoice = LegChoice.Primary

    Form(choice="Primary")
    Form()
    Form(choice=LegChoice.Primary)

    with raises(ValidationError):
        Form(choice="Wrong")


def test_choice_default_str():
    class LegChoice(Choice):
        Primary = "Primary"
        Secondary = "Secondary"

    class Form(FormPage):
        choice: LegChoice = "Primary"

    Form(choice="Primary")
    Form()
    Form(choice=LegChoice.Primary)

    with raises(ValidationError):
        Form(choice="Wrong")


def test_choice_schema():
    class LegChoice(Choice):
        Primary = "Primary"
        Secondary = "Secondary"

    class LegChoiceLabel(Choice):
        Primary = ("Primary", "Primary LP")
        Secondary = ("Secondary", "Secondary LP")
        Tertiary = "Tertiary"

    class Form(FormPage):
        choice: LegChoice
        choice_label: LegChoiceLabel

    expected = {
        "additionalProperties": False,
        "definitions": {
            "LegChoice": {
                "description": "An enumeration.",
                "enum": ["Primary", "Secondary"],
                "title": "LegChoice",
                "type": "string",
            },
            "LegChoiceLabel": {
                "description": "An enumeration.",
                "enum": ["Primary", "Secondary", "Tertiary"],
                "options": {"Primary": "Primary LP", "Secondary": "Secondary LP", "Tertiary": "Tertiary"},
                "title": "LegChoiceLabel",
                "type": "string",
            },
        },
        "properties": {
            "choice": {"$ref": "#/definitions/LegChoice"},
            "choice_label": {"$ref": "#/definitions/LegChoiceLabel"},
        },
        "required": ["choice", "choice_label"],
        "title": "unknown",
        "type": "object",
    }

    assert Form.model_json_schema() == expected
