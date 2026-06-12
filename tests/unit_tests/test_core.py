from typing import Optional

import pytest
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from pydantic_forms.core import FormPage, generate_form, post_form
from pydantic_forms.exceptions import FormNotCompleteError, FormOverflowError, FormValidationError
from pydantic_forms.types import strEnum

# TODO: Remove when generic forms of pydantic_forms are ready
from pydantic_forms.utils.json import json_dumps, json_loads


class TestChoices(strEnum):
    A = "a"
    B = "b"


class TestForm(FormPage):
    generic_select: TestChoices


def test_post_process_yield():
    def input_form(state):
        user_input = yield TestForm
        return user_input.model_dump() | {"extra": 234}

    validated_data = post_form(input_form, {"previous": True}, [{"generic_select": "a"}])

    expected = {"generic_select": "a", "extra": 234}
    assert json_loads(json_dumps(validated_data)) == expected


def test_post_process_extra_data():
    def input_form(state):
        user_input = yield TestForm
        return user_input.model_dump() | {"extra": 234}

    with pytest.raises(FormValidationError) as e:
        post_form(input_form, {"previous": True}, [{"generic_select": "a", "extra_data": False}])

    expected = "1 validation error for TestForm\nextra_data\n  Extra inputs are not permitted (type=extra_forbidden)"
    assert str(e.value) == expected


def test_post_process_validation_errors():
    def input_form(state):
        user_input = yield TestForm
        return user_input.model_dump()

    with pytest.raises(FormValidationError) as e:
        post_form(input_form, {}, [{"generic_select": 1, "extra_data": False}])

    expected = "2 validation errors for TestForm\ngeneric_select\n  Input should be 'a' or 'b' (type=enum; expected='a' or 'b')\nextra_data\n  Extra inputs are not permitted (type=extra_forbidden)"
    assert str(e.value) == expected

    with pytest.raises(FormValidationError) as e:
        post_form(input_form, {}, [{"generic_select": "c"}])

    expected = (
        "1 validation error for TestForm\ngeneric_select\n  Input should be 'a' or 'b' (type=enum; expected='a' or 'b')"
    )
    assert str(e.value) == expected


def test_post_form_wizard():
    # Return if there is no form
    assert post_form(None, {}, []) == {}
    assert post_form([], {}, []) == {}

    def input_form(state):
        class TestForm1(FormPage):
            model_config = ConfigDict(title="Some title")

            generic_select1: TestChoices

        class TestForm2(FormPage):
            generic_select2: TestChoices

        class TestForm3(FormPage):
            generic_select3: TestChoices

        user_input_1 = yield TestForm1

        if user_input_1.generic_select1 == TestChoices.A:
            user_input_2 = yield TestForm2
        else:
            user_input_2 = yield TestForm3

        return {**user_input_1.model_dump(), **user_input_2.model_dump()}

    # Submit 1
    with pytest.raises(FormNotCompleteError) as error_info:
        post_form(input_form, {"previous": True}, [])

    assert error_info.value.form == {
        "title": "Some title",
        "type": "object",
        "additionalProperties": False,
        "$defs": {
            "TestChoices": {
                "enum": ["a", "b"],
                "title": "TestChoices",
                "type": "string",
            }
        },
        "properties": {"generic_select1": {"$ref": "#/$defs/TestChoices"}},
        "required": ["generic_select1"],
    }

    # Submit 2
    with pytest.raises(FormNotCompleteError) as error_info:
        post_form(input_form, {"previous": True}, [{"generic_select1": "b"}])

    assert error_info.value.form == {
        "title": "unknown",
        "type": "object",
        "additionalProperties": False,
        "$defs": {
            "TestChoices": {
                "enum": ["a", "b"],
                "title": "TestChoices",
                "type": "string",
            }
        },
        "properties": {"generic_select3": {"$ref": "#/$defs/TestChoices"}},
        "required": ["generic_select3"],
    }

    # Submit complete
    validated_data = post_form(input_form, {"previous": True}, [{"generic_select1": "b"}, {"generic_select3": "a"}])

    expected = {"generic_select1": "b", "generic_select3": "a"}
    assert expected == json_loads(json_dumps(validated_data))

    # Submit overcomplete
    with pytest.raises(FormOverflowError, match="1 remaining"):
        post_form(
            input_form, {"previous": True}, [{"generic_select1": "b"}, {"generic_select3": "a"}, {"to_much": True}]
        )


def test_generate_form():
    def input_form(state):
        class TestForm1(FormPage):
            model_config = ConfigDict(title="Some title")

            generic_select1: TestChoices

        class TestForm2(FormPage):
            generic_select2: TestChoices

        class TestForm3(FormPage):
            generic_select3: TestChoices

        user_input_1 = yield TestForm1

        if user_input_1.generic_select1 == TestChoices.A:
            user_input_2 = yield TestForm2
        else:
            user_input_2 = yield TestForm3

        return {**user_input_1.model_dump(), **user_input_2.model_dump()}

    # Submit 1
    form = generate_form(input_form, {"previous": True}, [])

    assert form == {
        "title": "Some title",
        "type": "object",
        "additionalProperties": False,
        "$defs": {
            "TestChoices": {
                "enum": ["a", "b"],
                "title": "TestChoices",
                "type": "string",
            }
        },
        "properties": {"generic_select1": {"$ref": "#/$defs/TestChoices"}},
        "required": ["generic_select1"],
    }

    # Submit 2
    form = generate_form(input_form, {"previous": True}, [{"generic_select1": "b"}])

    assert form == {
        "title": "unknown",
        "type": "object",
        "additionalProperties": False,
        "$defs": {
            "TestChoices": {
                "enum": ["a", "b"],
                "title": "TestChoices",
                "type": "string",
            }
        },
        "properties": {"generic_select3": {"$ref": "#/$defs/TestChoices"}},
        "required": ["generic_select3"],
    }

    # Submit complete
    form = generate_form(input_form, {"previous": True}, [{"generic_select1": "b"}, {"generic_select3": "a"}])
    assert form is None


def test_loc():
    def form_generator(state):
        class Form1(FormPage):
            a: int

            @model_validator(mode="before")
            @classmethod
            def validator(cls, values: dict) -> dict:
                if values["a"] > 5:
                    raise ValueError("too high")
                return values

        yield Form1

        return {}

    with pytest.raises(FormValidationError) as e:
        post_form(form_generator, {}, [{"a": 6}])

    assert len(e.value.errors) == 1
    assert e.value.errors[0]["loc"] == ("__root__",)
    assert e.value.errors[0]["msg"] == "too high"


class SubModel(BaseModel):
    enabled: bool = False
    setting_when_enabled: Optional[int] = None

    @model_validator(mode="after")
    def only_when_enabled(self) -> "SubModel":
        if not self.enabled and self.setting_when_enabled is not None:
            raise ValueError("Yowch!")
        return self


class NestedSubModel(BaseModel):
    settings: SubModel


@pytest.mark.parametrize(
    "form_field_annotation, user_input, expected_loc",
    [
        (SubModel, {"enabled": False, "setting_when_enabled": 1}, ("nested", "__root__")),
        (Optional[SubModel], {"enabled": False, "setting_when_enabled": 1}, ("nested", "__root__")),
        (list[SubModel], [{"enabled": False, "setting_when_enabled": 1}], ("nested", 0, "__root__")),
        (dict[str, SubModel], {"key": {"enabled": False, "setting_when_enabled": 1}}, ("nested", "key", "__root__")),
        (
            NestedSubModel,
            {"settings": {"enabled": False, "setting_when_enabled": 1}},
            ("nested", "settings", "__root__"),
        ),
    ],
)
def test_loc_nested_model_validator(form_field_annotation, user_input, expected_loc):
    """Custom errors raised by a model_validator on a nested model are marked as model-level ("__root__") errors."""

    def form_generator(state):
        class Form(FormPage):
            nested: form_field_annotation

        yield Form

        return {}

    with pytest.raises(FormValidationError) as e:
        post_form(form_generator, {}, [{"nested": user_input}])

    assert len(e.value.errors) == 1
    assert e.value.errors[0]["loc"] == expected_loc
    assert e.value.errors[0]["msg"] == "Yowch!"


def test_loc_nested_model_field_errors_are_not_remapped():
    """Errors on leaf fields and non-validator errors on nested models keep their original location."""

    def form_generator(state):
        class Form(FormPage):
            nested: SubModel
            a: int

            @field_validator("a")
            @classmethod
            def validate_a(cls, value: int) -> int:
                if value > 5:
                    raise ValueError("too high")
                return value

        yield Form

        return {}

    # A ValueError on a leaf field keeps pointing at that field
    with pytest.raises(FormValidationError) as e:
        post_form(form_generator, {}, [{"nested": {"enabled": True}, "a": 6}])

    assert len(e.value.errors) == 1
    assert e.value.errors[0]["loc"] == ("a",)
    assert e.value.errors[0]["msg"] == "too high"

    # A missing nested model is not a custom validator error and keeps pointing at the nested model
    with pytest.raises(FormValidationError) as e:
        post_form(form_generator, {}, [{"a": 1}])

    assert len(e.value.errors) == 1
    assert e.value.errors[0]["loc"] == ("nested",)
    assert e.value.errors[0]["type"] == "missing"
