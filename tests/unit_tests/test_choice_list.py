from pydantic_core import ValidationError
from pytest import raises

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

    with raises(ValidationError):
        Form(choice=["Wrong"])

    with raises(ValidationError):
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

    with raises(ValidationError):
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

    with raises(ValidationError):
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

    assert Form.model_json_schema() == {
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


def test_choice_list_constraints():
    class LegChoice(Choice):
        Primary = "Primary"
        Secondary = "Secondary"

    class Form(FormPage):
        choice: choice_list(LegChoice, min_items=1, unique_items=True) = ["Primary"]

    m = Form(choice=[LegChoice.Primary, LegChoice.Secondary])
    assert m.choice == [LegChoice.Primary, LegChoice.Secondary]

    with raises(ValidationError) as exc_info:
        Form(choice=[1, 1, 1])
    assert exc_info.value.errors() == [
        {"loc": ("choice",), "msg": "the list has duplicated items", "type": "value_error.list.unique_items"}
    ]

    with raises(ValidationError) as exc_info:
        Form(choice=1)
    assert exc_info.value.errors() == [
        {"loc": ("choice",), "msg": "value is not a valid list", "type": "type_error.list"}
    ]

    with raises(ValidationError) as exc_info:
        Form(choice=[])
    assert exc_info.value.errors() == [
        {
            "loc": ("choice",),
            "msg": "ensure this value has at least 1 items",
            "type": "value_error.list.min_items",
            "ctx": {"limit_value": 1},
        }
    ]
