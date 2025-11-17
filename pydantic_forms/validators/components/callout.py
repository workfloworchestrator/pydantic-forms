# Copyright 2019-2025 SURF.
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
from enum import Enum
from functools import partial
from types import new_class
from typing import Annotated, Any, ClassVar, TypedDict, Union

from pydantic import BaseModel, Field


class CalloutMessageType(str, Enum):
    PRIMARY = "primary"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    ACCENT = "accent"


class CalloutData(TypedDict, total=False):
    header: Union[str, None]
    message: Union[str, None]
    icon_type: Union[str, None]
    message_type: Union[CalloutMessageType, str]


class _Callout(BaseModel):
    data: ClassVar[Union[CalloutData, None]] = None


Callout = Annotated[_Callout, Field(frozen=True, default=None, validate_default=False)]


def create_callout_schema(data: CalloutData, schema: dict[str, Any]) -> None:
    schema.update(
        {
            "format": "callout",
            "type": "string",
            "default": data,
        }
    )


def callout(
    *,
    header: Union[str, None] = None,
    message: Union[str, None] = None,
    icon_type: Union[str, None] = "info",
    message_type: Union[CalloutMessageType, str] = CalloutMessageType.PRIMARY,
) -> type[Callout]:

    data: CalloutData = {
        "header": header,
        "message": message,
        "icon_type": icon_type,
        "message_type": message_type,
    }

    namespace = {"data": data}
    klass: type[Callout] = new_class("CalloutValue", (_Callout,), {}, lambda ns: ns.update(namespace))

    json_schema_extra = partial(create_callout_schema, data)

    return Annotated[
        klass,
        Field(frozen=True, default=None, validate_default=False, json_schema_extra=json_schema_extra),
    ]  # type: ignore
