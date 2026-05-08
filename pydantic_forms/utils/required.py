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
from collections.abc import Iterable
from typing import (
    Annotated,
    Any,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

from more_itertools import first
from pydantic import BaseModel
from pydantic.fields import FieldInfo


def is_union(tp: type[Any] | None) -> bool:
    return tp is Union or tp is types.UnionType  # type: ignore[comparison-overlap]


def get_origin_and_args(t: Any) -> tuple[Any, tuple[Any, ...]]:
    """Return the origin and args of the given type.

    When wrapped in Annotated[] this is removed.
    """
    origin, args = get_origin(t), get_args(t)
    if origin is not Annotated:
        return origin, args

    t_unwrapped = first(args)
    return get_origin(t_unwrapped), get_args(t_unwrapped)


def is_union_type(t: Any, test_type: type | None = None) -> bool:
    """Check if `t` is union type (Union[Type, AnotherType]).

    Optionally check if T is of `test_type` We cannot check for literal Nones.

    >>> is_union_type(Union[int, str])
    True
    >>> is_union_type(Annotated[Union[int, str], "foo"])
    True
    >>> is_union_type(Union[int, str], str)
    True
    >>> is_union_type(Union[int, str], bool)
    False
    >>> is_union_type(Union[int, str], Union[int, str])
    True
    >>> is_union_type(Union[int, None])
    True
    >>> is_union_type(Annotated[Union[int, None], "foo"])
    True
    >>> is_union_type(int)
    False
    """
    origin, args = get_origin_and_args(t)
    if not is_union(origin):
        return False
    if not test_type:
        return True

    if is_of_type(t, test_type):
        return True

    for arg in args:
        result = is_of_type(arg, test_type)
        if result:
            return result
    return False


def is_of_type(t: Any, test_type: Any) -> bool:
    """Check if annotation type is valid for type.

    >>> is_of_type(list, list)
    True
    >>> is_of_type(list[int], list[int])
    True
    >>> is_of_type(strEnum, str)
    True
    >>> is_of_type(strEnum, Enum)
    True
    >>> is_of_type(int, str)
    False
    >>> is_of_type(Any, Any)
    True
    >>> is_of_type(Any, int)
    True
    """
    if t is Any:
        return True

    if is_union_type(test_type):
        return any(get_origin(t) is get_origin(arg) for arg in get_args(test_type))

    if (
        get_origin(t)
        and get_origin(test_type)
        and get_origin(t) is get_origin(test_type)
        and get_args(t) == get_args(test_type)
    ):
        return True

    if test_type is t:
        # Test type is a typing type instance and matches
        return True

    # Workaround for the fact that you can't call issubclass on typing types
    try:
        return issubclass(t, test_type)
    except TypeError:
        return False


def filter_nonetype(types_: Iterable[Any]) -> Iterable[Any]:
    def not_nonetype(type_: Any) -> bool:
        return type_ is not None.__class__

    return filter(not_nonetype, types_)


def is_optional_type(t: Any, test_type: type | None = None) -> bool:
    """Check if `t` is optional type (Union[None, ...]).

    And optionally check if T is of `test_type`

    >>> is_optional_type(Optional[int])
    True
    >>> is_optional_type(Annotated[Optional[int], "foo"])
    True
    >>> is_optional_type(Annotated[int, "foo"])
    False
    >>> is_optional_type(Union[None, int])
    True
    >>> is_optional_type(Union[int, str, None])
    True
    >>> is_optional_type(Union[int, str])
    False
    >>> is_optional_type(Optional[int], int)
    True
    >>> is_optional_type(Optional[int], str)
    False
    >>> is_optional_type(Annotated[Optional[int], "foo"], int)
    True
    >>> is_optional_type(Annotated[Optional[int], "foo"], str)
    False
    >>> is_optional_type(Optional[State], int)
    False
    >>> is_optional_type(Optional[State], State)
    True
    """
    origin, args = get_origin_and_args(t)

    if is_union(origin) and None.__class__ in args:
        field_type = first(filter_nonetype(args))
        return test_type is None or is_of_type(field_type, test_type)
    return False


# TODO The above code is copy-pasted from orchestrator-core/types.py.
#  Maybe something to move to a shared lib some day.


def _is_required(field: FieldInfo) -> bool:
    """Determine whether a FormPage field is required.

    Extends Pydantic's notion of "required" because FormPage is also used to *transmit* data.
    A field with a non-None default is still something the user is expected to confirm, so we
    treat it as required.
    Exceptions: a default of None means truly optional.
    """
    match field.annotation, field.is_required(), field.default, field.json_schema_extra:
        case _, True, _, _:
            # Pydantic considers the field as required
            return True
        case _, False, None, _:
            # Pydantic considers the field as optional, and the default is None.
            # Display-only types Label, Divider, Hidden, callout, migration_summary are
            # frozen with default=None and fall through here.
            return False
        case _, _, _, {"format": "read_only_field"}:
            # read_only_field is the one display-only marker that carries a non-None default and
            # isn't frozen, so it needs its own arm. New display-only markers should follow that
            # pattern (frozen + default=None) or be added here.
            return False
        case t, _, _, _:
            # A field is required if it's not optional (makes sense, doesn't it?)
            return not is_optional_type(t)
        case _:
            # For any combination we've missed, the safest assumption is that it's not required
            return False


BaseModelDerivative = TypeVar("BaseModelDerivative", bound=BaseModel)


def determine_required_form_fields(form: type[BaseModelDerivative]) -> dict[str, bool]:
    return {name: _is_required(field) for name, field in form.model_fields.items()}
