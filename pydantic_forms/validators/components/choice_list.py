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

from annotated_types import MaxLen, MinLen

from pydantic_forms.validators.components.choice import Choice

T = TypeVar("T")  # pragma: no mutate


def choice_list(
    item_type: type[Choice],
    *,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
) -> type[list[Choice]]:
    if unique_items:
        from pydantic_forms.validators import unique_conlist

        return unique_conlist(item_type, min_items=min_items, max_items=max_items)

    # Note: min_items always need to be there to remain backward compatible with frontend components
    if max_items:
        return Annotated[  # type: ignore[return-value]
            list[item_type],  # type:ignore[valid-type]
            MinLen(min_items or 0),
            MaxLen(max_items),
        ]

    return Annotated[  # type: ignore[return-value]
        list[item_type],  # type:ignore[valid-type]
        MinLen(min_items or 0),
    ]
