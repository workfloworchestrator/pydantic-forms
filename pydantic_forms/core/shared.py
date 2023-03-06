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
from inspect import isasyncgenfunction, isgeneratorfunction
from typing import Any, Callable, Dict, Generator, List, Optional

import structlog
from pydantic import BaseModel, Extra, Field
from pydantic.fields import ModelField, Undefined

from pydantic_forms.utils.json import json_dumps, json_loads

logger = structlog.get_logger(__name__)


class DisplayOnlyFieldType:
    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.nothing

    def nothing(cls, v: Any, field: ModelField) -> Any:
        return field.default


class FormPage(BaseModel):
    class Config:
        json_loads = json_loads
        json_dumps = json_dumps
        title = "unknown"
        extra = Extra.forbid
        validate_all = True

    def __init_subclass__(cls, /, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # The default and requiredness of a field is not a property of a field
        # In the case of DisplayOnlyFieldTypes, we do kind of want that.
        # Using this method we set the right properties after the form is created
        for field in cls.__fields__.values():
            try:
                if issubclass(field.type_, DisplayOnlyFieldType):
                    field.required = False
                    field.allow_none = True
            except TypeError:
                pass


def ReadOnlyField(
    default: Any = Undefined,
    *,
    const: Optional[bool] = None,
    **extra: Any,
) -> Any:
    return Field(default, const=True, uniforms={"disabled": True, "value": default}, **extra)  # type: ignore


FORMS: Dict[str, Callable] = {}


def register_form(key: str, form: Callable) -> None:
    logger.info("Current Forms", forms=FORMS, new_key=key)
    if key in FORMS and form is not FORMS[key]:
        raise Exception(f"Trying to re-register form {key} with a different function")

    if not isasyncgenfunction(form) and not isgeneratorfunction(form):
        raise Exception(f"Trying to register form {key} function {form} which is not an (async) generator function")

    FORMS[key] = form


def list_forms() -> List[str]:
    return list(FORMS.keys())
