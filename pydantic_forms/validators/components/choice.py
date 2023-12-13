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
from typing import Any, ClassVar, Optional

from pydantic import GetJsonSchemaHandler
from pydantic_core import CoreSchema

from pydantic_forms.types import strEnum


class Choice(strEnum):
    """Let the user choose from an enum and submit the label.

    As of March 2023 mypy does not yet support functional API on Enum subclasses
    https://github.com/python/mypy/issues/6037

    This means that:
        MyChoice1 = Choice("MyChoice1", {"option1": "value1", "option2": "value2"})

    Will result in the (invalid) mypy error
        error: Argument 2 to "Choice" has incompatible type "Dict[str, str]"; expected "Optional[str]"  [arg-type]

    Because it maps to Choice.__new__ instead of Enum.__call__

    Workaround is to be explicit:
        MyChoice1 = Choice.__call__("MyChoice1", {"option1": "value1", "option2": "value2"})
    """

    label: ClassVar[str]

    def __new__(cls, value: str, label: Optional[str] = None) -> "Choice":
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.label = label or value  # type:ignore
        return obj

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, Any]:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)

        # Next lines are a bit of a hack to make sure we always get an enum for uniforms.
        # A better solution is to rewrite this whole class to a functional approach with a serializer
        if single_choice := json_schema.get("const"):
            json_schema["enum"] = [single_choice]
            json_schema.pop("const")

        kwargs = {}

        options = {i.value: i.label for i in cls.__members__.values()}

        if not all((value == label for value, label in options.items())):
            kwargs["options"] = options

        return json_schema | {"type": "string"} | kwargs
