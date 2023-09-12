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
from typing import Any, ClassVar, Optional, Type

from pydantic import BaseModel, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import CoreSchema, core_schema

from pydantic_forms.core import DisplayOnlyFieldType
from pydantic_forms.types import SummaryData


# class MigrationSummary(DisplayOnlyFieldType):
class MigrationSummary(BaseModel):
    data: ClassVar[Optional[SummaryData]] = None

    # @classmethod
    # def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
    #     return core_schema.no_info_after_validator_function(cls, handler(DisplayOnlyFieldType))

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, Any]:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)

        return json_schema | {"format": "summary", "type": "string", "uniforms": {"data": cls.data}}

    # @classmethod
    # def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
    #     field_schema.update(format="summary", type="string", uniforms={"data": cls.data})


def migration_summary(data: Optional[SummaryData] = None) -> Type[MigrationSummary]:
    namespace = {"data": data}
    return new_class("MigrationSummaryValue", (MigrationSummary,), {}, lambda ns: ns.update(namespace))
