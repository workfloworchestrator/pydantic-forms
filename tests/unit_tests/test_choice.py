from uuid import UUID

import pytest
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
        "$defs": {
            "LegChoice": {
                "enum": ["Primary", "Secondary"],
                "title": "LegChoice",
                "type": "string",
            },
            "LegChoiceLabel": {
                "enum": ["Primary", "Secondary", "Tertiary"],
                "options": {"Primary": "Primary LP", "Secondary": "Secondary LP", "Tertiary": "Tertiary"},
                "title": "LegChoiceLabel",
                "type": "string",
            },
        },
        "properties": {
            "choice": {"$ref": "#/$defs/LegChoice"},
            "choice_label": {"$ref": "#/$defs/LegChoiceLabel"},
        },
        "required": ["choice", "choice_label"],
        "title": "unknown",
        "type": "object",
    }

    assert Form.model_json_schema() == expected


def test_choice_uuids():
    uuids = [
        UUID("3a3691e2-399a-4733-8924-2cb524eb4723"),
        UUID("efadf3f8-da32-475e-8dad-6efffa901bae"),
        UUID("8724775d-2bfa-43e0-b861-942aa8699e1e"),
    ]
    choices = {str(u): f"choice {num} is uuid {u}" for num, u in enumerate(uuids, start=1)}

    UUIDChoice = Choice("UUIDChoice", zip(choices, choices.items()))

    class Form(FormPage):
        choice: UUIDChoice

    first_uuid = uuids[0]
    validated = Form(choice=str(first_uuid))
    assert validated.model_dump() == {"choice": str(first_uuid)}

    # Cannot use the actual UUID because it's a strEnum
    with pytest.raises(
        ValidationError,
        match=r"choice\n\s+Input should be '3a3691e2-399a-4733-8924-2cb524eb4723', 'efadf3f8-da32-475e-8dad-6efffa901bae' or '8724775d-2bfa-43e0-b861-942aa8699e1e'",
    ):
        Form(choice=first_uuid)
