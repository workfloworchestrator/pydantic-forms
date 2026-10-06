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
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Final, Literal

from annotated_types import GroupedMetadata
from pydantic import Field, JsonValue

# Fixed: the pydantic-forms frontend renders a 12-column grid and clamps span and start to it
GRID_COLUMNS: Final = 12

LayoutAlign = Literal["start", "center", "end", "stretch"]


@dataclass(frozen=True)
class Layout(GroupedMetadata):
    """Position a field on the 12-column form grid, e.g. `Annotated[str, Layout(span=6)]`.

    Adds a camelCase `layout` object to the field's JSON schema.
    Fields without one take the full width.

    Args:
        span: Width in columns (1-12), full width when unset.
        start: Column (1-12) to start at, leaves the columns before it empty.
        new_row: Always start on a new row, even when the current row has space left.
        row_span: Height in rows, one row when unset. The following fields are placed next to it.
        align: Vertical position of the field within its row.
    """

    span: int | None = None
    start: int | None = None
    new_row: bool = False
    row_span: int | None = None
    align: LayoutAlign | None = None

    def __post_init__(self) -> None:
        if self.span is not None and not 1 <= self.span <= GRID_COLUMNS:
            raise ValueError(f"span must be between 1 and {GRID_COLUMNS}")
        if self.start is not None and not 1 <= self.start <= GRID_COLUMNS:
            raise ValueError(f"start must be between 1 and {GRID_COLUMNS}")
        if self.start is not None and self.start + (self.span or 1) - 1 > GRID_COLUMNS:
            raise ValueError(f"start + span exceeds the {GRID_COLUMNS} column grid")
        if self.row_span is not None and self.row_span < 1:
            raise ValueError("row_span must be at least 1")

    def __iter__(self) -> Iterator[object]:
        options: dict[str, JsonValue] = {
            "span": self.span,
            "start": self.start,
            "newRow": self.new_row or None,
            "rowSpan": self.row_span,
            "align": self.align,
        }
        layout: dict[str, JsonValue] = {key: value for key, value in options.items() if value}
        # An empty Layout() is the same as no Layout, the field takes the full width
        if layout:
            yield Field(json_schema_extra={"layout": layout})
