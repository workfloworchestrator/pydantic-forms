# Copyright 2019-2023 SURF.
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
from typing import Annotated, Any, Hashable, List, Optional, Type, TypeVar, get_args

from pydantic import AfterValidator, Field, GetCoreSchemaHandler, GetJsonSchemaHandler, conlist
from pydantic.v1 import ConstrainedList
from pydantic_core import CoreSchema, PydanticCustomError, core_schema

T = TypeVar("T", bound=Hashable)


class UniqueConstrainedList(ConstrainedList, list[T]):
    unique_items: Optional[bool] = None

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, Any]:
        json_schema = handler.resolve_ref_schema(core_schema["schema"])
        return json_schema

    # @classmethod
    # def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
    #     super().__modify_schema__(field_schema)
    #     update_not_none(field_schema, uniqueItems=cls.unique_items)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls._validate, handler(list))

    @classmethod
    def _validate(cls, value: Any) -> "UniqueConstrainedList":
        # Ugly since we would like to just call the base class validation, but ConstrainedList is deprecated
        cls.list_length_validator(value)

        if cls.unique_items is not None:
            value = cls.check_unique(value)

        return UniqueConstrainedList(value)

    @classmethod
    def check_unique(cls, v: list[T]) -> list[T]:
        if len(set(v)) != len(v):
            raise ValueError("Items must be unique")

        return v

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Copy generic argument (T) if not set explicitly
        # This makes a lot of assuptions about the internals of `typing`
        if "__orig_bases__" in cls.__dict__ and cls.__dict__["__orig_bases__"]:
            generic_base_cls = cls.__dict__["__orig_bases__"][0]
            if (not hasattr(cls, "item_type") or isinstance(cls.item_type, TypeVar)) and get_args(generic_base_cls):
                cls.item_type = get_args(generic_base_cls)[0]

        # Make sure __args__ is set
        assert hasattr(cls, "item_type"), "Missing a concrete value for generic type argument"  # noqa: S101

        cls.__args__ = (cls.item_type,)

    def __class_getitem__(cls, key: Any) -> Any:
        # Some magic to make sure that subclasses of this class still work as expected
        class Inst(cls):  # type: ignore
            item_type = key
            __args__ = (key,)

        return Inst


def _validate_unique_list(v: list[T]) -> list[T]:
    if len(v) != len(set(v)):
        raise PydanticCustomError("unique_list", "List must be unique")
    return v


def unique_conlist(
    item_type: Type[T],
    *,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
) -> Type[List[T]]:
    return Annotated[
        conlist(item_type, min_length=min_items, max_length=max_items),
        AfterValidator(_validate_unique_list),
        Field(json_schema_extra={"uniqueItems": True}),
    ]
