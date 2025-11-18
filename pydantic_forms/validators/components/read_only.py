# Copyright 2019-2025 SURF, ESnet.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import sys
from itertools import chain
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AfterValidator, BeforeValidator, Field, PlainSerializer, TypeAdapter

from pydantic_forms.types import strEnum
from pydantic_forms.utils.schema import merge_json_schema

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


def _get_read_only_schema(default: Any) -> dict:
    """Get base schema dict object for uniforms."""
    return {"uniforms": {"disabled": True, "value": default}, "type": _get_json_type(default)}


def read_only_list(default: list[Any] | None = None) -> Any:
    """Create type with json schema of type array that is 'read only'."""
    if not isinstance(default, list):
        raise ValueError("Default argument must be a list")

    # Empty list is valid, but needs a type
    if len(default) == 0:
        default_item_type: Any = str
    else:
        item_types = {type(item) for item in default}
        if len(item_types) != 1:
            raise TypeError("All items in read_only_list must be of same type")

        default_item_type = list(item_types)[0]

    if default_item_type is type(None):
        raise TypeError("read_only_list item type cannot be 'NoneType'")

    json_schema = _get_read_only_schema(default)

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
        Field(default, json_schema_extra=json_schema),
        AfterValidator(validate_list),
        PlainSerializer(serialize_list, when_used="json"),
    ]


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
    json_schema = _get_read_only_schema(default)

    if isinstance(default, list):
        raise TypeError(f"Use {read_only_list.__name__}")

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
        Field(default, json_schema_extra=json_schema),
        BeforeValidator(validate),
        PlainSerializer(serialize_json, when_used="json"),
    ]
    if merge_type is not None:
        return merge_json_schema(read_only_type, merge_type)
    return read_only_type
