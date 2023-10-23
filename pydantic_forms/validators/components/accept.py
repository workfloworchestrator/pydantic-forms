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
from typing import Any, ClassVar, Optional

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.v1.errors import EnumMemberError
from pydantic_core import CoreSchema, PydanticCustomError, core_schema

from pydantic_forms.types import AcceptData, strEnum


class Accept(str):
    data: ClassVar[Optional[AcceptData]] = None

    class Values(strEnum):
        ACCEPTED = "ACCEPTED"
        INCOMPLETE = "INCOMPLETE"

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, Any]:
        json_schema = handler.resolve_ref_schema(core_schema["schema"])
        return (
            json_schema
            | {"format": "accept", "type": "string", "enum": list(cls.Values)}
            | ({"data": cls.data} if cls.data else {})
        )

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls._validate, handler(str))

    @classmethod
    def _validate(cls, value: str) -> str:
        value = cls.enum_validator(value)
        cls.must_be_complete(value)
        return value

    @classmethod
    def enum_validator(cls, v: Any) -> str:
        try:
            enum_v = cls.Values(v)
        except ValueError:
            # cls.Values should be an enum, so will be iterable
            enum_values = list(cls.Values)
            # TODO: this converts the deprecated v1 error to a generic error. Not clear yet how to handle this in
            # the future
            orig = EnumMemberError(enum_values=enum_values)
            raise PydanticCustomError(f"type_error.{orig.code}", str(orig), {"enum_values": enum_values})
        return enum_v.value

    @classmethod
    def must_be_complete(cls, v: str) -> bool:
        if v == "INCOMPLETE":
            raise ValueError("Not all tasks are done")

        return v == "ACCEPTED"
