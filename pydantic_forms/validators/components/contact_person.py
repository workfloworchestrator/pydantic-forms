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
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

# class ContactPersonName(str):
#     @classmethod
#     def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
#         return core_schema.no_info_after_validator_function(cls, handler(str))
#
#     @classmethod
#     def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, Any]:
#         json_schema = handler.resolve_ref_schema(core_schema)
#         json_schema["format"] = "contactPersonName"
#         return json_schema


ContactPersonName = Annotated[str, Field(json_schema_extra={"format": "contactPersonName"})]


class ContactPerson(BaseModel):
    name: ContactPersonName
    email: EmailStr
    phone: str = ""
