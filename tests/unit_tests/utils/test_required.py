from typing import Annotated

from inline_snapshot import snapshot
from pydantic import Field

from pydantic_forms.core import FormPage
from pydantic_forms.settings import pydantic_form_settings
from pydantic_forms.utils.required import determine_required_form_fields
from pydantic_forms.validators import (
    Divider,
    Hidden,
    Label,
    callout,
    migration_summary,
    read_only_field,
    read_only_list,
)


class FormWithAllDefaultScenarios(FormPage):
    int_no_default: int
    int_with_default: int = 1
    nullable_int_no_default: int | None  # Probably not used
    nullable_int_default_none: int | None = None  # Dito
    nullable_int_with_default: int | None = 1

    list_no_default: list[int]
    list_default_factory: list[int] = Field(default_factory=list)
    list_with_default: list[int] = [1, 2, 3]
    constrained_list_with_default: Annotated[list[int], Field(min_length=1)] = [1, 2, 3]

    bool_no_default: bool
    bool_with_default: bool = True


def test_difference_between_default_and_extended_handling(monkeypatch):
    """Extended handling promotes fields with a default value (or default_factory) to required."""
    default_required = set(FormWithAllDefaultScenarios.model_json_schema()["required"])

    monkeypatch.setattr(pydantic_form_settings, "REQUIRED_FIELD_HANDLING", "extended")
    extended_required = set(FormWithAllDefaultScenarios.model_json_schema()["required"])

    assert extended_required - default_required == snapshot(
        {
            "int_with_default",
            "list_default_factory",
            "list_with_default",
            "constrained_list_with_default",
            "bool_with_default",
        }
    )


def test_schema_with_default_handling():
    """Under default handling, only fields without a default are listed as required."""
    assert FormWithAllDefaultScenarios.model_json_schema() == snapshot(
        {
            "additionalProperties": False,
            "properties": {
                "int_no_default": {"title": "Int No Default", "type": "integer"},
                "int_with_default": {"default": 1, "title": "Int With Default", "type": "integer"},
                "nullable_int_no_default": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "title": "Nullable Int No Default",
                },
                "nullable_int_default_none": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "default": None,
                    "title": "Nullable Int Default None",
                },
                "nullable_int_with_default": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "default": 1,
                    "title": "Nullable Int With Default",
                },
                "list_no_default": {"items": {"type": "integer"}, "title": "List No Default", "type": "array"},
                "list_default_factory": {
                    "items": {"type": "integer"},
                    "title": "List Default Factory",
                    "type": "array",
                },
                "list_with_default": {
                    "default": [1, 2, 3],
                    "items": {"type": "integer"},
                    "title": "List With Default",
                    "type": "array",
                },
                "constrained_list_with_default": {
                    "default": [1, 2, 3],
                    "items": {"type": "integer"},
                    "minItems": 1,
                    "title": "Constrained List With Default",
                    "type": "array",
                },
                "bool_no_default": {"title": "Bool No Default", "type": "boolean"},
                "bool_with_default": {"default": True, "title": "Bool With Default", "type": "boolean"},
            },
            "required": ["int_no_default", "nullable_int_no_default", "list_no_default", "bool_no_default"],
            "title": "unknown",
            "type": "object",
        }
    )


def test_schema_with_extended_handling(monkeypatch):
    """Under extended handling, fields with a default are also marked required, except nullable ones."""
    monkeypatch.setattr(pydantic_form_settings, "REQUIRED_FIELD_HANDLING", "extended")

    assert FormWithAllDefaultScenarios.model_json_schema() == snapshot(
        {
            "additionalProperties": False,
            "properties": {
                "int_no_default": {"title": "Int No Default", "type": "integer"},
                "int_with_default": {"default": 1, "title": "Int With Default", "type": "integer"},
                "nullable_int_no_default": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "title": "Nullable Int No Default",
                },
                "nullable_int_default_none": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "default": None,
                    "title": "Nullable Int Default None",
                },
                "nullable_int_with_default": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "default": 1,
                    "title": "Nullable Int With Default",
                },
                "list_no_default": {"items": {"type": "integer"}, "title": "List No Default", "type": "array"},
                "list_default_factory": {
                    "items": {"type": "integer"},
                    "title": "List Default Factory",
                    "type": "array",
                },
                "list_with_default": {
                    "default": [1, 2, 3],
                    "items": {"type": "integer"},
                    "title": "List With Default",
                    "type": "array",
                },
                "constrained_list_with_default": {
                    "default": [1, 2, 3],
                    "items": {"type": "integer"},
                    "minItems": 1,
                    "title": "Constrained List With Default",
                    "type": "array",
                },
                "bool_no_default": {"title": "Bool No Default", "type": "boolean"},
                "bool_with_default": {"default": True, "title": "Bool With Default", "type": "boolean"},
            },
            "required": [
                "int_no_default",
                "int_with_default",
                "nullable_int_no_default",
                "list_no_default",
                "list_default_factory",
                "list_with_default",
                "constrained_list_with_default",
                "bool_no_default",
                "bool_with_default",
            ],
            "title": "unknown",
            "type": "object",
        }
    )


def test_determine_required_form_fields():
    """Per-field requiredness as computed by the extended-handling helper, independent of settings."""
    requireds = determine_required_form_fields(FormWithAllDefaultScenarios)

    assert requireds == snapshot(
        {
            "int_no_default": True,
            "int_with_default": True,
            "nullable_int_no_default": True,
            "nullable_int_default_none": False,
            "nullable_int_with_default": False,
            "list_no_default": True,
            "list_default_factory": True,
            "list_with_default": True,
            "constrained_list_with_default": True,
            "bool_no_default": True,
            "bool_with_default": True,
        }
    )


class FormWithDisplayOnlyFields(FormPage):
    label_with_default: Label = None
    divider_with_default: Divider = None
    hidden_with_default: Hidden = None
    label_no_default: Label
    divider_no_default: Divider
    hidden_no_default: Hidden
    callout_field: callout(message="hi")
    summary_field: migration_summary({"headers": [], "columns": []})
    read_only_str: read_only_field("value")
    read_only_int: read_only_field(42)
    read_only_lst: read_only_list([1, 2, 3])


def test_display_only_fields_are_never_required():
    """Display-only and read-only validators must not be marked required, with or without an explicit default."""
    assert determine_required_form_fields(FormWithDisplayOnlyFields) == snapshot(
        {
            "label_with_default": False,
            "divider_with_default": False,
            "hidden_with_default": False,
            "label_no_default": False,
            "divider_no_default": False,
            "hidden_no_default": False,
            "callout_field": False,
            "summary_field": False,
            "read_only_str": False,
            "read_only_int": False,
            "read_only_lst": False,
        }
    )
