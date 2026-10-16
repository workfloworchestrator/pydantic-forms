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

from typing import Any, Iterable, Union, get_args

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


def inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Replace each local ``$ref`` by the ``$defs`` entry it points to, so a reader needs no lookup.

    The keys beside a ``$ref`` (a field's own ``title``, ``default``, ``readOnly``) win over the definition's.
    A reference that is part of a cycle, a model that contains itself, is left as it is and its definition is
    kept under ``$defs``; when no such reference remains, ``$defs`` is dropped.
    """
    defs: dict[str, Any] = schema.get("$defs") or {}
    kept: set[str] = set()

    def expand(node: Any, stack: tuple[str, ...]) -> Any:
        match node:
            case {"$ref": str() as ref, **siblings} if (name := _local_definition(ref)) in defs:
                if name in stack:
                    kept.add(name)
                    return node
                return {**expand(defs[name], (*stack, name)), **expand(siblings, stack)}
            case dict():
                return {key: expand(value, stack) for key, value in node.items()}
            case list():
                return [expand(item, stack) for item in node]
            case _:
                return node

    result = expand({key: value for key, value in schema.items() if key != "$defs"}, ())
    kept_defs: dict[str, Any] = {}
    while pending := kept - kept_defs.keys():  # a kept definition may itself refer to another one
        kept_defs.update({name: expand(defs[name], (name,)) for name in pending})
    return {**result, "$defs": kept_defs} if kept_defs else result


def _local_definition(ref: str) -> Union[str, None]:
    """The name a ``#/$defs/<name>`` reference points to; None for any other reference."""
    prefix = "#/$defs/"
    return ref[len(prefix) :] if ref.startswith(prefix) else None
