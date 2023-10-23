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
from typing import Optional, TypeVar

from pydantic import AfterValidator, Field, conlist
from pydantic_core import PydanticCustomError
from typing_extensions import Annotated

from pydantic_forms.validators.components.choice import Choice

T = TypeVar("T")  # pragma: no mutate


def choice_list(
    item_type: type[Choice],
    *,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
) -> type[list[T]]:
    def _validate_unique_list(v: list[T]) -> list[T]:
        if unique_items and len(v) != len(set(v)):
            raise PydanticCustomError("unique_list", "List must be unique")
        return v

    schema_extra = {"uniqueItems": unique_items} if unique_items is not None else {}
    return Annotated[  # type: ignore[return-value]
        conlist(item_type, min_length=min_items, max_length=max_items),
        AfterValidator(_validate_unique_list),
        Field(json_schema_extra=schema_extra),
    ]
