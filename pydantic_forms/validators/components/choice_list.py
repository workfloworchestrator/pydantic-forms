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
from typing import List, Optional, Type, TypeVar, Annotated

from pydantic import conlist, Field, AfterValidator
from pydantic_core import PydanticCustomError

from pydantic_forms.validators.components.choice import Choice

T = TypeVar("T")  # pragma: no mutate


# class ChoiceList(UniqueConstrainedList[T]):
#     @classmethod
#     def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
#         super().__modify_schema__(field_schema)
#
#         data: dict = {}
#         cls.item_type.__modify_schema__(data)  # type: ignore
#         field_schema.update(**{k: v for k, v in data.items() if k == "options"})


def choice_list(
    item_type: Type[Choice],
    *,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
) -> Type[List[T]]:
    def _validate_unique_list(v: list[T]) -> list[T]:
        if unique_items and len(v) != len(set(v)):
            raise PydanticCustomError("unique_list", "List must be unique")
        return v

    return Annotated[
        conlist(item_type, min_length=min_items, max_length=max_items),
        AfterValidator(_validate_unique_list),
        Field(json_schema_extra={"uniqueItems": True}),
    ]
