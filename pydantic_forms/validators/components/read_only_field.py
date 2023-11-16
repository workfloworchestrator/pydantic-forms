import sys
from itertools import chain
from typing import Annotated, Any, Literal, Union
from uuid import UUID

from pydantic import BeforeValidator, Field, PlainSerializer, TypeAdapter

from pydantic_forms.types import strEnum

# from pydantic.json_schema
JSON_SCHEMA_TYPES = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
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


def ReadOnlyField(default: Union[UUID, strEnum, int, bool, str, bytes]) -> Any:
    dynamic_validator = None
    if isinstance(default, STRINGY_TYPES):
        dynamic_validator = TypeAdapter(default.__class__)

    def validate(v: Any) -> Any:
        if dynamic_validator:
            return dynamic_validator.validate_python(v)
        return v

    def serialize_json(_v: Any) -> str:
        if not isinstance(default, str):
            return str(default)
        return default

    json_schema = {"uniforms": {"disabled": True, "value": default}, "type": _get_json_type(default)}

    return Annotated[
        Literal[default],
        Field(default, json_schema_extra=json_schema),
        BeforeValidator(validate),
        PlainSerializer(serialize_json, when_used="json"),
    ]
