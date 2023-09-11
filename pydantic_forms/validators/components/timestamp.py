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
from typing import Any, ClassVar, Optional

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema


class Timestamp(int):
    show_time_select: ClassVar[Optional[bool]] = True
    locale: ClassVar[Optional[str]] = None  # example: nl-nl
    min: ClassVar[Optional[int]] = None
    max: ClassVar[Optional[int]] = None
    date_format: ClassVar[Optional[str]] = None  # example: DD-MM-YYYY HH:mm
    time_format: ClassVar[Optional[str]] = None  # example: HH:mm

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(int))

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        return json_schema | {
            "format": "timestamp",
            "type": "number",
            "uniforms": {
                # Using JS naming convention to increase DX on the JS side
                "showTimeSelect": cls.show_time_select,
                "locale": cls.locale,
                "min": cls.min,
                "max": cls.max,
                "dateFormat": cls.date_format,
                "timeFormat": cls.time_format,
            },
        }


def timestamp(
    show_time_select: Optional[bool] = True,
    locale: Optional[str] = None,
    min: Optional[int] = None,
    max: Optional[int] = None,
    date_format: Optional[str] = None,
    time_format: Optional[str] = None,
) -> type[Timestamp]:
    namespace = {
        "show_time_select": show_time_select,
        "locale": locale,
        "min": min,
        "max": max,
        "date_format": date_format,
        "time_format": time_format,
    }
    return new_class("TimestampValue", (Timestamp,), {}, lambda ns: ns.update(namespace))
