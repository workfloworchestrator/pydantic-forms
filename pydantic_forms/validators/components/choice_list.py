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
from types import new_class
from typing import Any, List, Optional, Type, TypeVar

from pydantic_forms.validators.components.choice import Choice
from pydantic_forms.validators.components.unique_constrained_list import UniqueConstrainedList

T = TypeVar("T")  # pragma: no mutate


class ChoiceList(UniqueConstrainedList[T]):
    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        super().__modify_schema__(field_schema)

        data: dict = {}
        cls.item_type.__modify_schema__(data)  # type: ignore
        field_schema.update(**{k: v for k, v in data.items() if k == "options"})


def choice_list(
    item_type: Type[Choice],
    *,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
) -> Type[List[T]]:
    namespace = {
        "min_items": min_items,
        "max_items": max_items,
        "unique_items": unique_items,
        "__origin__": list,  # Needed for pydantic to detect that this is a list
        "item_type": item_type,  # Needed for pydantic to detect the item type
        "__args__": (item_type,),  # Needed for pydantic to detect the item type
    }
    # We use new_class to be able to deal with Generic types
    return new_class(
        "ChoiceListValue", (ChoiceList[item_type],), {}, lambda ns: ns.update(namespace)  # type:ignore
    )
