from __future__ import annotations

import sys
from itertools import chain
from typing import Annotated, Any, Iterable, Literal, get_args
from uuid import UUID

from more_itertools import first
from pydantic import AfterValidator, BeforeValidator, Field, PlainSerializer, TypeAdapter
from pydantic.fields import FieldInfo

from pydantic_forms.types import strEnum

# from pydantic.json_schema
JSON_SCHEMA_TYPES = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    type(None): "string",
    list: "array",
}


if sys.version_info >= (3, 11):
    from enum import StrEnum

    STRINGY_TYPES = (StrEnum, strEnum, UUID)
else:
    STRINGY_TYPES = (strEnum, UUID)


def _get_json_type(default: Any) -> str:
    if isinstance(default, STRINGY_TYPES):
        return JSON_SCHEMA_TYPES[str]

    type_ = type(default)
    try:
        return JSON_SCHEMA_TYPES[type_]
    except KeyError:
        types = ", ".join(t.__name__ for t in chain(JSON_SCHEMA_TYPES, STRINGY_TYPES))
        raise TypeError(f"Cannot make a read_only_field for type {type_}. Supported types: {types}")


def read_only_list(default: list[Any]) -> Any:
    """Create type with json schema of type array that is 'read only'."""
    if len(default) == 0:
        raise ValueError("Default list object must not be empty")

    item_types = {type(item) for item in default}
    if len(item_types) != 1:
        raise TypeError("All items in read_only_list must be of same type")

    default_item_type: Any = list(item_types)[0]
    if default_item_type is type(None):
        raise TypeError("read_only_list item type cannot be 'NoneType'")

    json_schema = {"uniforms": {"disabled": True, "value": default}, "type": _get_json_type(default)}

    def validate_list(value: list) -> list:
        if value == default:
            return value

        raise ValueError("Cannot change values for a readonly list")

    def serialize_list(list_: Any) -> list:
        def to_value(item: Any) -> Any:
            return str(item) if isinstance(item, UUID) else item

        return [to_value(item) for item in list_]

    return Annotated[
        list[default_item_type],
        Field(default, json_schema_extra=json_schema),  # type: ignore[arg-type]
        AfterValidator(validate_list),
        PlainSerializer(serialize_list, when_used="json"),
    ]


# Helper utils
def _get_field_info_with_schema(type_: Any) -> Iterable[FieldInfo]:
    for annotation in get_args(type_):
        if isinstance(annotation, FieldInfo) and annotation.json_schema_extra:
            yield annotation


def merge_json_schema(source_type: Any, target_type: Any) -> Any:
    """Add json_schema from source_type to target_type."""
    if not (source_field_info := first(_get_field_info_with_schema(source_type), None)):
        raise TypeError("Source type has no json_schema_extra")
    if not (target_field_info := first(_get_field_info_with_schema(target_type), None)):
        raise TypeError("Target type has no json_schema_extra")
    source_schema = source_field_info.json_schema_extra
    target_schema = target_field_info.json_schema_extra

    if not isinstance(source_schema, dict) or not isinstance(target_schema, dict):
        raise TypeError(
            f"Cannot merge json_schema_extra of source_type {type(source_schema)} with target_type {type(target_type)}"
        )
    source_schema.update(target_schema)
    return source_type


def read_only_field(default: Any, merge_type: Any | None = None) -> Any:
    """Create type with json schema that sets frontend form field to active=false.

    Args:
    ----
        default(Any): value to display as inactive field on form
        merge_type(Any | None): merge another pydantic_form type for this field

    Returns:
    -------
        type annotation which will submit json schema with active=false to uniforms

    """
    json_schema = {"uniforms": {"disabled": True, "value": default}, "type": _get_json_type(default)}

    if isinstance(default, list):
        raise TypeError("Use read_only_list")

    dynamic_validator = TypeAdapter(default.__class__) if isinstance(default, STRINGY_TYPES) else None

    def validate(v: Any) -> Any:
        if dynamic_validator:
            return dynamic_validator.validate_python(v)
        return v

    def serialize_json(_v: Any) -> str:
        if not isinstance(default, str):
            return str(default)
        return default

    read_only_type = Annotated[
        Literal[default],  # type: ignore[valid-type]
        Field(default, json_schema_extra=json_schema),  # type: ignore[arg-type]
        BeforeValidator(validate),
        PlainSerializer(serialize_json, when_used="json"),
    ]
    if merge_type is not None:
        return merge_json_schema(read_only_type, merge_type)
    return read_only_type
