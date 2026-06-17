# Copyright 2019-2026 SURF.
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
import types
from functools import cache
from typing import Annotated, Any, TypeVar, Union, get_args, get_origin

from more_itertools import last
from pydantic import BaseModel, Field, TypeAdapter, ValidationError
from pydantic.fields import FieldInfo


def _is_optional_type(t: Any) -> bool:
    """Whether ``t`` is ``Union[..., None]`` (or ``X | None``).

    ``FieldInfo.annotation`` is already unwrapped by Pydantic (``Annotated`` metadata is
    stripped onto ``FieldInfo.metadata``), so a single-level ``get_origin`` check suffices.
    """
    return get_origin(t) in (Union, types.UnionType) and type(None) in get_args(t)


def _is_list_type(t: Any) -> bool:
    return get_origin(t) is list


def _has_positive_min_length(field: FieldInfo) -> bool:
    """Whether the field metadata declares ``min_length > 0``.

    Works for:
     - pydantic.Field(min_length=...)
     - annotated_types.MinLen(...)
     - annotated_types.Len(min_length=...)
    """
    min_lengths = (i for md in field.metadata if (i := getattr(md, "min_length", None)) is not None)
    if (min_length := last(min_lengths, None)) is not None:
        return min_length > 0

    return False


@cache
def _pattern_accepts_empty_string(pattern: str) -> bool:
    """Whether a regex pattern accepts ``""`` as evaluated by Pydantic."""
    try:
        TypeAdapter(Annotated[str, Field(pattern=pattern)]).validate_python("")
    except ValidationError:
        return False
    return True


def _has_pattern_allowing_empty_string(field: FieldInfo) -> bool:
    patterns = (pattern for md in field.metadata if (pattern := getattr(md, "pattern", None)) is not None)
    if (pattern := last(patterns, None)) is not None:
        return _pattern_accepts_empty_string(pattern)
    return True


def _empty_string_accepted(field: FieldInfo) -> bool:
    """Whether the string field's constraints."""
    return (not _has_positive_min_length(field)) and _has_pattern_allowing_empty_string(field)


def _empty_list_accepted(field: FieldInfo) -> bool:
    return not _has_positive_min_length(field)


def _is_required(field: FieldInfo) -> bool:
    """Determine whether a FormPage field is required.

    Extends Pydantic's notion of "required" because FormPage is also used to *transmit* data.
    A field with a non-None default is still something the user is expected to confirm, so we
    treat it as required.
    Exceptions: a default of None means truly optional. A list or string with a default is
    not required when its constraints accept emptiness (no ``min_length > 0`` and, for
    strings, no pattern that rejects ``""``).
    """
    match field.annotation, field.is_required(), field.default, field.json_schema_extra:
        case _, True, _, _:
            # Pydantic considers the field as required
            return True
        case _, False, None, _:
            # Pydantic considers the field as optional, and the default is None
            return False
        case _ if field.frozen:
            # Frozen fields can't be edited by users. If they somehow manage to, the submitted value is discarded.
            return False
        case _, _, _, {"format": "read_only_field"}:
            # read_only_field can't be edited by users. If they somehow manage to, validation will fail
            return False
        case type_, False, _, _ if _is_list_type(type_) and _empty_list_accepted(field):
            # As a list field can be left empty, perform a best-effort check whether this is allowed by pydantic
            return False
        case type_, False, _, _ if type_ is str and _empty_string_accepted(field):
            # As a string field can be left empty, perform a best-effort check whether this is allowed by pydantic
            return False
        case type_, _, _, _:
            # A field is required if it's not optional (makes sense, doesn't it?)
            return not _is_optional_type(type_)
        case _:
            # For any combination we've missed, the safest assumption is that it's not required
            return False


BaseModelDerivative = TypeVar("BaseModelDerivative", bound=BaseModel)


def determine_required_form_fields(form: type[BaseModelDerivative]) -> dict[str, bool]:
    return {name: _is_required(field) for name, field in form.model_fields.items()}
