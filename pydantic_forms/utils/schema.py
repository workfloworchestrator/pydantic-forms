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
