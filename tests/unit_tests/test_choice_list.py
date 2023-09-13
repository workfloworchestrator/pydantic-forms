import pytest
from pydantic_core import ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.validators import Choice, choice_list


def test_choice_list():
    class LegChoice(Choice):
        Primary = "Primary"
        Secondary = "Secondary"

    class Form(FormPage):
        choice: choice_list(LegChoice)

    # Validation works
    Form(choice=["Primary"])
    Form(choice=["Primary", "Primary"])

    with pytest.raises(ValidationError):
        Form(choice=["Wrong"])

    with pytest.raises(ValidationError):
        Form(choice=["Primary", "Wrong"])


def test_choice_list_default():
    class LegChoice(Choice):
        Primary = "Primary"
        Secondary = "Secondary"

    class Form(FormPage):
        choice: choice_list(LegChoice) = [LegChoice.Primary]

    Form(choice=["Primary"])
    Form()
    Form(choice=[LegChoice.Primary])

    with pytest.raises(ValidationError):
        Form(choice=["Wrong"])


def test_choice_list_default_str():
    class LegChoice(Choice):
        Primary = "Primary"
        Secondary = "Secondary"

    class Form(FormPage):
        choice: choice_list(LegChoice) = ["Primary"]

    Form(choice=["Primary"])
    Form()
    Form(choice=[LegChoice.Primary])

    with pytest.raises(ValidationError):
        Form(choice=["Wrong"])


def test_choice_list_schema():
    class LegChoice(Choice):
        Primary = "Primary"
        Secondary = "Secondary"

    class LegChoiceLabel(Choice):
        Primary = ("Primary", "Primary LP")
        Secondary = ("Secondary", "Secondary LP")
        Tertiary = "Tertiary"

    class Form(FormPage):
        choice: choice_list(LegChoice)
        choice_label: choice_list(LegChoiceLabel)

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
            "choice": {"items": {"$ref": "#/definitions/LegChoice"}, "type": "array"},
            "choice_label": {
                "items": {"$ref": "#/definitions/LegChoiceLabel"},
                "options": {"Primary": "Primary LP", "Secondary": "Secondary LP", "Tertiary": "Tertiary"},
                "type": "array",
            },
        },
        "required": ["choice", "choice_label"],
        "title": "unknown",
        "type": "object",
    }
    assert Form.model_json_schema() == expected


@pytest.fixture(name="Form")
def form_with_leg_choice_list():
    class LegChoice(Choice):
        Primary = "Primary"
        Secondary = "Secondary"

    class Form(FormPage):
        choice: choice_list(LegChoice, min_items=1, unique_items=True) = ["Primary"]

    return Form


def test_choice_list_constraint_should_be_unique(Form):
    with pytest.raises(ValidationError) as exc_info:
        Form(choice=[1, 1, 1])

    errors = exc_info.value.errors(include_url=False, include_context=False)
    expected = [
        {"input": [1, 1, 1], "loc": ("choice",), "msg": "Value error, Items must be unique", "type": "value_error"}
    ]
    assert errors == expected


def test_choice_list_constraint_invalid_list(Form):
    with pytest.raises(ValidationError) as exc_info:
        Form(choice=1)

    errors = exc_info.value.errors(include_url=False, include_context=False)
    expected = [{"input": 1, "loc": ("choice",), "msg": "Input should be a valid list", "type": "list_type"}]
    assert errors == expected


def test_choice_list_constraint_at_least_one_item(Form):
    with pytest.raises(ValidationError) as exc_info:
        Form(choice=[])

    errors = exc_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "input": [],
            "loc": ("choice",),
            "msg": "Value error, ensure this value has at least 1 items",
            "type": "value_error",
            # "ctx": {"limit_value": 1},
        }
    ]
    assert errors == expected
