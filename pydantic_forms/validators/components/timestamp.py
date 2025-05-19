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
from typing import Annotated, Any, Optional

from annotated_types import Interval
from pydantic import Field


def timestamp(
    show_time_select: Optional[bool] = True,
    locale: Optional[str] = None,
    validate: bool = True,  # Set to False to disable min/max validation
    min: Optional[int] = None,
    max: Optional[int] = None,
    date_format: Optional[str] = None,
    time_format: Optional[str] = None,
) -> Any:
    schema = Field(
        json_schema_extra={
            "format": "timestamp",
            "type": "number",
            "uniforms": {
                "showTimeSelect": show_time_select,
                "locale": locale,
                "min": min,
                "max": max,
                "dateFormat": date_format,
                "timeFormat": time_format,
            },
        }
    )

    if validate:
        return Annotated[int, Interval(ge=min, le=max), schema]
    return Annotated[int, schema]


Timestamp = timestamp()
