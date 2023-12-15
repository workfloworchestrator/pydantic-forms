from __future__ import annotations

import sys
from itertools import chain
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AfterValidator, BeforeValidator, Field, PlainSerializer, TypeAdapter

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
        raise TypeError(f"Cannot make a ReadOnlyField for type {type_}. Supported types: {types}")


def _read_only_list(default: Any, default_type: Any | None, json_schema: dict) -> Any:
    # TODO #16 change to a standalone generic type, i.e. read_only_list[str](["foo", "bar"])
    if default_type is None:
        raise TypeError("Need the default_type parameter when using ReadOnlyField for a list")

    def validate_list(value: list) -> list:
        if value == default:
            return value

        raise ValueError("Cannot change values for a readonly list")

    def serialize_list(list_: Any) -> list:
        def to_value(item: Any) -> Any:
            return str(item) if isinstance(item, UUID) else item

        return [to_value(item) for item in list_]

    return Annotated[
        default_type,
        Field(default, json_schema_extra=json_schema | {"const": default}),
        AfterValidator(validate_list),
        PlainSerializer(serialize_list, when_used="json"),
    ]


def ReadOnlyField(default: Any, default_type: Any | None = None) -> Any:
    # TODO #16 Change to read_only_field
    json_schema = {"uniforms": {"disabled": True, "value": default}, "type": _get_json_type(default)}

    if isinstance(default, list):
        return _read_only_list(default, default_type, json_schema)

    dynamic_validator = TypeAdapter(default.__class__) if isinstance(default, STRINGY_TYPES) else None

    def validate(v: Any) -> Any:
        if dynamic_validator:
            return dynamic_validator.validate_python(v)
        return v

    def serialize_json(_v: Any) -> str:
        if not isinstance(default, str):
            return str(default)
        return default

    return Annotated[
        Literal[default],
        Field(default, json_schema_extra=json_schema),  # type: ignore[arg-type]
        BeforeValidator(validate),
        PlainSerializer(serialize_json, when_used="json"),
    ]
