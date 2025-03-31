# Copyright 2019-2025 SURF, ESnet.
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

"""Helper utilities for dealing with json schema objects (json_schema_extra, etc)."""

from typing import Any, Iterable, get_args

from more_itertools import first
from pydantic.fields import FieldInfo


def _get_field_info_with_schema(type_: Any) -> Iterable[FieldInfo]:
    for annotation in get_args(type_):
        if isinstance(annotation, FieldInfo) and annotation.json_schema_extra:
            yield annotation


def merge_json_schema(source_type: Any, target_type: Any) -> Any:
    """Add json_schema from target_type to source_type."""
    if not (source_field_info := first(_get_field_info_with_schema(source_type), None)):
        raise TypeError("Source type has no json_schema_extra")
    if not (target_field_info := first(_get_field_info_with_schema(target_type), None)):
        raise TypeError("Target type has no json_schema_extra")
    source_schema = source_field_info.json_schema_extra
    target_schema = target_field_info.json_schema_extra

    source_schema.update(target_schema)  # type: ignore[union-attr,arg-type]
    return source_type
