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

from types import new_class
from typing import Any, ClassVar, Dict, Generator, List, Optional, Type, TypeVar, get_args
from uuid import UUID

import structlog
from pydantic import BaseModel, EmailStr, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.utils import update_not_none
from pydantic.v1 import ConstrainedList
from pydantic.v1.errors import EnumMemberError
from pydantic.v1.validators import uuid_validator
from pydantic_core import CoreSchema, core_schema

from pydantic_forms.core import DisplayOnlyFieldType
from pydantic_forms.types import AcceptData, SummaryData, strEnum

logger = structlog.get_logger(__name__)


T = TypeVar("T")  # pragma: no mutate


class UniqueConstrainedList(ConstrainedList, List[T]):
    unique_items: Optional[bool] = None

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        super().__modify_schema__(field_schema)
        update_not_none(field_schema, uniqueItems=cls.unique_items)

    @classmethod
    def __get_validators__(cls) -> Generator:  # noqa: B902
        yield from super().__get_validators__()
        if cls.unique_items is not None:
            yield cls.check_unique

    @classmethod
    def check_unique(cls, v: List[T]) -> List[T]:
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


def unique_conlist(
    item_type: Type[T],
    *,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
) -> Type[List[T]]:
    namespace = {
        "min_items": min_items,
        "max_items": max_items,
        "unique_items": unique_items,
        "__origin__": list,  # Needed for pydantic to detect that this is a list
        "__args__": (item_type,),  # Needed for pydantic to detect the item type
    }
    # We use new_class to be able to deal with Generic types
    return new_class(
        "ConstrainedListValue", (UniqueConstrainedList[item_type],), {}, lambda ns: ns.update(namespace)  # type:ignore
    )


def remove_empty_items(v: list) -> list:
    """Remove Falsy values from list.

    Sees dicts with all Falsy values as Falsy.
    This is used to allow people to submit list fields which are "empty" but are not really empty like:
    `[{}, None, {name:"", email:""}]`

    Example:
        >>> remove_empty_items([{}, None, [], {"a":""}])
        []
    """
    if v:
        return list(filter(lambda i: bool(i) and (not isinstance(i, dict) or any(i.values())), v))
    return v


class Accept(str):
    data: ClassVar[Optional[AcceptData]] = None

    class Values(strEnum):
        ACCEPTED = "ACCEPTED"
        INCOMPLETE = "INCOMPLETE"

    # @classmethod
    # def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
    #     field_schema.update(
    #         format="accept",
    #         type="string",
    #         enum=[v.value for v in cls.Values],
    #         **({"data": cls.data} if cls.data else {}),
    #     )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, Any]:
        json_schema = handler.resolve_ref_schema(core_schema["schema"])
        return (
            json_schema
            | {"format": "accept", "type": "string", "enum": [v for v in cls.Values]}
            | ({"data": cls.data} if cls.data else {})
        )

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls._validate, handler(str))

    @classmethod
    def _validate(cls, value: str) -> "Accept":
        value = cls.enum_validator(value)
        value = cls.must_be_complete(value)
        return Accept(value)

    @classmethod
    def enum_validator(cls, v: Any) -> str:
        try:
            enum_v = cls.Values(v)
        except ValueError:
            # cls.Values should be an enum, so will be iterable
            raise EnumMemberError(enum_values=list(cls.Values))
        return enum_v.value

    @classmethod
    def must_be_complete(cls, v: str) -> bool:
        if v == "INCOMPLETE":
            raise ValueError("Not all tasks are done")

        return v == "ACCEPTED"


class Choice(strEnum):
    """Let the user choose from an enum and submit the label.

    As of March 2023 mypy does not yet support functional API on Enum subclasses
    https://github.com/python/mypy/issues/6037

    This means that:
        MyChoice1 = Choice("MyChoice1", {"option1": "value1", "option2": "value2"})

    Will result in the (invalid) mypy error
        error: Argument 2 to "Choice" has incompatible type "Dict[str, str]"; expected "Optional[str]"  [arg-type]

    Because it maps to Choice.__new__ instead of Enum.__call__

    Workaround is to be explicit:
        MyChoice1 = Choice.__call__("MyChoice1", {"option1": "value1", "option2": "value2"})
    """

    label: ClassVar[str]

    def __new__(cls, value: str, label: Optional[str] = None) -> "Choice":
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.label = label or value  # type:ignore
        return obj

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        kwargs = {}

        options = dict(map(lambda i: (i.value, i.label), cls.__members__.values()))

        if not all(map(lambda o: o[0] == o[1], options.items())):
            kwargs["options"] = options

        field_schema.update(type="string", **kwargs)


class ChoiceList(UniqueConstrainedList[T]):
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        super().__modify_schema__(field_schema)

        data: dict = {}
        cls.item_type.__modify_schema__(data)  # type: ignore
        field_schema.update(**{k: v for k, v in data.items() if k == "options"})


def choice_list(
    item_type: Type[Choice],
    *,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
) -> Type[List[T]]:
    namespace = {
        "min_items": min_items,
        "max_items": max_items,
        "unique_items": unique_items,
        "__origin__": list,  # Needed for pydantic to detect that this is a list
        "item_type": item_type,  # Needed for pydantic to detect the item type
        "__args__": (item_type,),  # Needed for pydantic to detect the item type
    }
    # We use new_class to be able to deal with Generic types
    return new_class(
        "ChoiceListValue", (ChoiceList[item_type],), {}, lambda ns: ns.update(namespace)  # type:ignore
    )


class ContactPersonName(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, Any]:
        json_schema = handler.resolve_ref_schema(core_schema)
        json_schema["format"] = "contactPersonName"
        return json_schema


class ContactPerson(BaseModel):
    name: ContactPersonName
    email: EmailStr
    phone: str = ""


class ContactPersonList(ConstrainedList):
    item_type = ContactPerson
    __args__ = (ContactPerson,)

    organisation: ClassVar[Optional[UUID]] = None
    organisation_key: ClassVar[Optional[str]] = "organisation"

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        super().__modify_schema__(field_schema)
        data = {}

        if cls.organisation:
            data["organisationId"] = str(cls.organisation)
        if cls.organisation_key:
            data["organisationKey"] = cls.organisation_key

        field_schema.update(**data)

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield from super().__get_validators__()
        yield remove_empty_items


def contact_person_list(
    organisation: Optional[UUID] = None, organisation_key: Optional[str] = "organisation"
) -> Type[List[T]]:
    namespace = {"organisation": organisation, "organisation_key": organisation_key}
    # We use new_class to be able to deal with Generic types
    return new_class("ContactPersonListValue", (ContactPersonList,), {}, lambda ns: ns.update(namespace))


class LongText(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, Any]:
        json_schema = handler.resolve_ref_schema(core_schema["schema"])
        return json_schema | {"format": "long", "type": "string"}


class DisplaySubscription(DisplayOnlyFieldType):
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(format="subscription", type="string")


class Label(DisplayOnlyFieldType):
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(format="label", type="string")


class Divider(DisplayOnlyFieldType):
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(format="divider", type="string")


class OrganisationId(UUID):
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(format="organisationId")

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield uuid_validator


class MigrationSummary(DisplayOnlyFieldType):
    data: ClassVar[Optional[SummaryData]] = None

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(format="summary", type="string", uniforms={"data": cls.data})


def migration_summary(data: Optional[SummaryData] = None) -> Type[MigrationSummary]:
    namespace = {"data": data}
    return new_class("MigrationSummaryValue", (MigrationSummary,), {}, lambda ns: ns.update(namespace))


class ListOfOne(UniqueConstrainedList[T]):
    min_items = 1
    max_items = 1


class ListOfTwo(UniqueConstrainedList[T]):
    min_items = 2
    max_items = 2


class Timestamp(int):
    show_time_select: ClassVar[Optional[bool]] = True
    locale: ClassVar[Optional[str]] = None  # example: nl-nl
    min: ClassVar[Optional[int]] = None
    max: ClassVar[Optional[int]] = None
    date_format: ClassVar[Optional[str]] = None  # example: DD-MM-YYYY HH:mm
    time_format: ClassVar[Optional[str]] = None  # example: HH:mm

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(
            format="timestamp",
            type="number",
            uniforms={
                # Using JS naming convention to increase DX on the JS side
                "showTimeSelect": cls.show_time_select,
                "locale": cls.locale,
                "min": cls.min,
                "max": cls.max,
                "dateFormat": cls.date_format,
                "timeFormat": cls.time_format,
            },
        )


def timestamp(
    show_time_select: Optional[bool] = True,
    locale: Optional[str] = None,
    min: Optional[int] = None,
    max: Optional[int] = None,
    date_format: Optional[str] = None,
    time_format: Optional[str] = None,
) -> Type[Timestamp]:
    namespace = {
        "show_time_select": show_time_select,
        "locale": locale,
        "min": min,
        "max": max,
        "date_format": date_format,
        "time_format": time_format,
    }
    return new_class("TimestampValue", (Timestamp,), {}, lambda ns: ns.update(namespace))
