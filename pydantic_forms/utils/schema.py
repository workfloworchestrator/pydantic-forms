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

from collections.abc import Iterator
from dataclasses import dataclass
from itertools import chain
from typing import Any, Iterable, Union, get_args

from more_itertools import first
from pydantic.fields import FieldInfo

from pydantic_forms.utils.pointer import escape, parse_pointer

# The keyword a field carries to say where its options are fetched, and the key inside it that maps each ``{name}``
# in the URL to a pointer into the page's data. Emitted by ``pydantic_forms.validators.OptionsSource``.
OPTIONS_SOURCE = "optionsSource"
DEPENDS_ON = "dependsOn"


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
    A reference that is part of a cycle, a model that contains itself, is left as it is. ``$defs`` keeps the
    definitions still referred to, by such a reference or by a discriminator ``mapping``, and is dropped when empty.

    >>> inline_refs(
    ...     {
    ...         "properties": {"port": {"$ref": "#/$defs/Port", "title": "Uplink"}},
    ...         "$defs": {"Port": {"type": "string", "title": "Port"}},
    ...     }
    ... )
    {'properties': {'port': {'type': 'string', 'title': 'Uplink'}}}
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
            case {"discriminator": {"mapping": dict() as mapping}}:
                kept.update(_definitions_named_in(mapping, defs))
                return {key: expand(value, stack) for key, value in node.items()}
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


def _definitions_named_in(mapping: dict[str, Any], defs: dict[str, Any]) -> set[str]:
    """The ``$defs`` entries a discriminator ``mapping`` points to."""
    return {name for name in map(_local_definition, mapping.values()) if name is not None and name in defs}


def _local_definition(ref: str) -> Union[str, None]:
    """The name a ``#/$defs/<name>`` reference points to; None for any other reference."""
    prefix = "#/$defs/"
    return ref[len(prefix) :] if ref.startswith(prefix) else None


@dataclass(frozen=True)
class Located:
    """A node of a page schema, where it is, and the schemas of the values on the way down to it."""

    location: str
    """A JSON Pointer into the schema, such as ``/properties/ports/items/properties/node``."""
    lineage: tuple[dict[str, Any], ...]
    """The schema of each value from the page down to the node's own, which comes last: what a relative pointer counts."""

    @property
    def schema(self) -> dict[str, Any]:
        return self.lineage[-1]


def nodes_with(schema: dict[str, Any], key: str) -> Iterator[Located]:
    """Every node of a page schema that carries ``key``, with its location and lineage.

    ``properties``, ``items`` and ``prefixItems`` each describe a value one level below their node; an ``anyOf`` or
    ``oneOf`` branch describes the same value. References are not followed: inline them first with ``inline_refs``.

    >>> tuple(node.location for node in nodes_with({"properties": {"a": {"x": 1, "items": {"x": 2}}}}, "x"))
    ('/properties/a', '/properties/a/items')
    """
    return _walk(schema, key, "", (schema,))


_BRANCHES = ("anyOf", "oneOf")


def _walk(node: dict[str, Any], key: str, location: str, lineage: tuple[dict[str, Any], ...]) -> Iterator[Located]:
    here = [Located(location, lineage)] if key in node else []
    properties: dict[str, Any] = node.get("properties") or {}
    down = chain(
        ((f"properties/{escape(name)}", child) for name, child in properties.items()),
        (("items", node.get("items")),),
        ((f"prefixItems/{index}", child) for index, child in enumerate(node.get("prefixItems") or ())),
    )
    walked = chain(
        (_walk(child, key, f"{location}/{path}", (*lineage, child)) for path, child in down if isinstance(child, dict)),
        (
            _walk(child, key, f"{location}/{path}", (*lineage[:-1], child))
            for path, child in _branches(node)
            if isinstance(child, dict)
        ),
    )
    return chain(here, chain.from_iterable(walked))


def _branches(node: dict[str, Any]) -> list[tuple[str, Any]]:
    """The ``anyOf`` and ``oneOf`` subschemas of a node, each with its path: the same value, described another way."""
    return [
        (f"{keyword}/{index}", branch) for keyword in _BRANCHES for index, branch in enumerate(node.get(keyword) or ())
    ]


def resolve_pointer(node: Located, pointer: str) -> Union[dict[str, Any], None]:
    """The schema of the value a pointer points at, from the value ``node`` describes; None when there is none.

    A JSON Pointer starts at the page, a Relative JSON Pointer at the node and goes up its lineage first. Then a
    member name goes through ``properties``, an index or ``-`` through ``items`` or ``prefixItems``, and an ``anyOf``
    or ``oneOf`` branch is looked through.
    """
    if (parsed := parse_pointer(pointer)) is None:
        return None
    if parsed.levels_up is None:
        return _descend(node.lineage[0], parsed.segments)
    if parsed.levels_up >= len(node.lineage):
        return None
    return _descend(node.lineage[-1 - parsed.levels_up], parsed.segments)


def _descend(schema: dict[str, Any], segments: tuple[str, ...]) -> Union[dict[str, Any], None]:
    if not segments:
        return schema
    head, rest = segments[0], segments[1:]
    match schema:
        case {"properties": dict() as properties} if head in properties:
            return _descend(properties[head], rest)
        case {"items": dict() as items} if head == "-" or head.isdigit():
            return _descend(items, rest)
        case {"prefixItems": list() as items} if head.isdigit() and int(head) < len(items):
            return _descend(items[int(head)], rest)
        case _:
            found = (_descend(branch, segments) for _, branch in _branches(schema) if isinstance(branch, dict))
            return first(filter(None, found), None)


def options_sources(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """The sourced fields of a page by their location in the schema, each with its ``optionsSource``.

    A location is a JSON Pointer into the schema, ``/properties/ports/items/properties/node``, so a field inside a
    nested model or a list item is found as well as one on the page. The result is the same whether or not the
    schema's ``$defs`` were inlined.

    >>> options_sources(
    ...     {
    ...         "properties": {
    ...             "codes": {"type": "array", "items": {"type": "string", "optionsSource": {"url": "/codes"}}},
    ...             "name": {"type": "string"},
    ...         }
    ...     }
    ... )
    {'/properties/codes/items': {'url': '/codes'}}
    """
    return {node.location: node.schema[OPTIONS_SOURCE] for node in _sourced(schema)}


def check_options_sources(schema: dict[str, Any], page_name: str) -> None:
    """Raise ``ValueError`` when a source's ``dependsOn`` pointer points at no field of the page.

    Every pointer of every sourced field, inside nested models and list items too, is resolved against the
    schema. A form author's bug, so the message names the page, the field's location and the pointer.
    """
    if problems := list(chain.from_iterable(map(_unresolved, _sourced(schema)))):
        raise ValueError(f"{page_name}: {'; '.join(problems)}")


def _sourced(schema: dict[str, Any]) -> Iterator[Located]:
    return nodes_with(inline_refs(schema), OPTIONS_SOURCE)


def _unresolved(node: Located) -> list[str]:
    """One line per ``dependsOn`` pointer of a sourced field that points at no field."""
    pointers = node.schema[OPTIONS_SOURCE].get(DEPENDS_ON) or {}
    return [
        f"{node.location} fills {name!r} from {pointer!r}, which points at no field"
        for name, pointer in pointers.items()
        if resolve_pointer(node, pointer) is None
    ]
