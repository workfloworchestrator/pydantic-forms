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
from typing import Annotated, Optional, TypeVar

from annotated_types import Len
from more_itertools import all_unique
from pydantic import AfterValidator, Field
from pydantic_core import PydanticCustomError

T = TypeVar("T")


def validate_unique_list(values: list[T]) -> list[T]:
    if not all_unique(values):
        raise PydanticCustomError("unique_list", "List must be unique")
    return values


def unique_conlist(
    item_type: type[T],
    *,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
) -> type[list[T]]:
    return Annotated[  # type: ignore[return-value]
        list[item_type],  # type: ignore[valid-type]  # sssh
        AfterValidator(validate_unique_list),
        Len(min_items or 0, max_items),
        Field(json_schema_extra={"uniqueItems": True}),
    ]
