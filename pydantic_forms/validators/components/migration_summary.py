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
from functools import partial
from types import new_class
from typing import Annotated, Any, ClassVar, Optional

from pydantic import BaseModel, Field

from pydantic_forms.types import SummaryData


class _MigrationSummary(BaseModel):
    data: ClassVar[Optional[SummaryData]] = None


MigrationSummary = Annotated[_MigrationSummary, Field(frozen=True, default=None, validate_default=False)]


def create_json_extra_schema(data: SummaryData, schema: dict[str, Any]) -> None:
    schema.update({"format": "summary", "type": "string", "uniforms": {"data": data}})
    schema.pop("allOf")  # This is needed, because otherwise Uniforms (3.8.1) is unable to render this schema


def migration_summary(data: SummaryData) -> type[MigrationSummary]:
    namespace = {"data": data}
    klass: type[MigrationSummary] = new_class(
        "MigrationSummaryValue", (_MigrationSummary,), {}, lambda ns: ns.update(namespace)
    )

    json_schema_extra = partial(create_json_extra_schema, data)

    return Annotated[
        klass, Field(frozen=True, default=None, validate_default=False, json_schema_extra=json_schema_extra)
    ]  # type: ignore
