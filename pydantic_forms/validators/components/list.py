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

from typing import TypeVar

from pydantic import Field

T = TypeVar("T")


def MinItems(min_items: int):
    """Annotator for minimum number of items in a list."""
    return Field(min_items=min_items)


def MaxItems(max_items: int):
    """Annotator for maximum number of items in a list."""
    return Field(max_items=max_items)


def ItemLength(min_items: int | None = None, max_items: int | None = None):
    """Annotator for both minimum and maximum number of items."""
    return Field(min_items=min_items, max_items=max_items)
