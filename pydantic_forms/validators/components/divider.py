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
from typing import Any

from pydantic import GetJsonSchemaHandler
from pydantic_core import CoreSchema

from pydantic_forms.core import DisplayOnlyFieldType


class Divider(DisplayOnlyFieldType):
    # @classmethod
    # def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
    #     field_schema.update(format="divider", type="string")

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, Any]:
        json_schema = handler.resolve_ref_schema(core_schema["schema"])
        return json_schema | {"format": "divider", "type": "string"}
