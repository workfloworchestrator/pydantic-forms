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
from typing import Annotated, Any, ClassVar, Optional, Type, TypeVar, Generator
from uuid import UUID

from pydantic import Field, GetCoreSchemaHandler, GetJsonSchemaHandler, conlist
from pydantic.v1 import ConstrainedList
from pydantic_core import CoreSchema, core_schema

from pydantic_forms.validators.components.contact_person import ContactPerson

T = TypeVar("T")  # pragma: no mutate


# class ContactPersonList(ConstrainedList):
#     item_type = ContactPerson
#     __args__ = (ContactPerson,)
#
#     organisation: ClassVar[Optional[UUID]] = None
#     organisation_key: ClassVar[Optional[str]] = "organisation"
#
#     @classmethod
#     def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
#         return core_schema.no_info_after_validator_function(remove_empty_items, handler(list))
#
#     @classmethod
#     def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, Any]:
#         json_schema = handler.resolve_ref_schema(core_schema)
#
#         data = {}
#
#         if cls.organisation:
#             data["organisationId"] = str(cls.organisation)
#         if cls.organisation_key:
#             data["organisationKey"] = cls.organisation_key
#
#         json_schema.update(**data)
#
#         return json_schema


def contact_person_list(
    organisation: Optional[UUID] = None,
    organisation_key: Optional[str] = "organisation",
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
) -> Type[list[T]]:
    def json_schema_extra() -> Generator:
        if organisation:
            yield "organisation", organisation
        if organisation_key:
            yield "organisation_key", organisation_key

    return Annotated[
        conlist(ContactPerson, min_length=min_items, max_length=max_items),
        Field(json_schema_extra=dict(json_schema_extra())),
    ]  # type: ignore


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
