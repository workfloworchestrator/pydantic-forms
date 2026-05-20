# Copyright 2019-2026 SURF.
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


class MarkdownColor(str, Enum):
    PRIMARY = "primary"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    ACCENT = "accent"


class MarkdownData(TypedDict, total=False):
    content: Union[str, None]
    color: Union[MarkdownColor, str]


class _Markdown(BaseModel):
    data: ClassVar[Union[MarkdownData, None]] = None


Markdown = Annotated[_Markdown, Field(frozen=True, default=None, validate_default=False)]


def create_markdown_schema(data: MarkdownData, schema: dict[str, Any]) -> None:
    schema.update(
        {
            "format": "markdown",
            "type": "string",
            "default": data,
        }
    )


def markdown(
    *,
    content: Union[str, None] = None,
    color: Union[MarkdownColor, str] = MarkdownColor.PRIMARY,
) -> type[Markdown]:

    data: MarkdownData = {
        "content": content,
        "color": color,
    }

    namespace = {"data": data}
    klass: type[Markdown] = new_class("MarkdownValue", (_Markdown,), {}, lambda ns: ns.update(namespace))

    json_schema_extra = partial(create_markdown_schema, data)

    return Annotated[
        klass,
        Field(frozen=True, default=None, validate_default=False, json_schema_extra=json_schema_extra),
    ]  # type: ignore
