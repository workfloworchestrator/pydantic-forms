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

from typing import Annotated

from pydantic import AfterValidator, Field

from pydantic_forms.validators.components.unique_constrained_list import T, validate_unique_list

ListOfTwo = Annotated[
    list[T],
    AfterValidator(validate_unique_list),
    Field(min_length=2, max_length=2, json_schema_extra={"uniqueItems": True}),
]
