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
from typing import Any, ClassVar, Generator, List, Optional, Type, TypeVar
from uuid import UUID

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.v1 import ConstrainedList
from pydantic_core import CoreSchema, core_schema

from pydantic_forms.validators import ContactPerson

T = TypeVar("T")  # pragma: no mutate


class ContactPersonList(ConstrainedList):
    item_type = ContactPerson
    __args__ = (ContactPerson,)

    organisation: ClassVar[Optional[UUID]] = None
    organisation_key: ClassVar[Optional[str]] = "organisation"

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(remove_empty_items, handler(List))

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, Any]:
        json_schema = handler.resolve_ref_schema(core_schema)

        data = {}

        if cls.organisation:
            data["organisationId"] = str(cls.organisation)
        if cls.organisation_key:
            data["organisationKey"] = cls.organisation_key

        json_schema.update(**data)

        return json_schema

    # @classmethod
    # def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
    #     # super().__modify_schema__(field_schema)
    #     data = {}
    #
    #     if cls.organisation:
    #         data["organisationId"] = str(cls.organisation)
    #     if cls.organisation_key:
    #         data["organisationKey"] = cls.organisation_key

    # field_schema.update(**data)

    # @classmethod
    # def __get_validators__(cls) -> Generator:
    #     # yield from super().__get_validators__()
    #     yield remove_empty_items


def contact_person_list(
    organisation: Optional[UUID] = None, organisation_key: Optional[str] = "organisation"
) -> Type[List[T]]:
    namespace = {"organisation": organisation, "organisation_key": organisation_key}
    # We use new_class to be able to deal with Generic types
    return new_class("ContactPersonListValue", (ContactPersonList,), {}, lambda ns: ns.update(namespace))


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
