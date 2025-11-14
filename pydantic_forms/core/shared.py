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
from typing import Any, Callable

import structlog
from pydantic import BaseModel, ConfigDict, PydanticUndefinedAnnotation, version

logger = structlog.get_logger(__name__)


PYDANTIC_VERSION = version.version_short()


class DisplayOnlyFieldType:
    pass


class FormPage(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        title="unknown",
        extra="forbid",
        validate_default=True,
    )

    def __init__(self, **data: Any):
        frozen_fields = {k: v for k, v in self.__class__.model_fields.items() if v.frozen}

        def get_value(k: str, v: Any) -> Any:
            if k in frozen_fields:
                return frozen_fields[k].default
            return v

        mutable_data = {k: get_value(k, v) for k, v in data.items()}
        super().__init__(**mutable_data)

    if PYDANTIC_VERSION in ("2.9", "2.10", "2.11"):

        @classmethod
        def __pydantic_init_subclass__(cls, /, **kwargs: Any) -> None:
            # The default and requiredness of a field is not a property of a field
            # In the case of DisplayOnlyFieldTypes, we do kind of want that.
            # Using this method we set the right properties after the form is created
            needs_rebuild = False

            for field in cls.model_fields.values():
                if field.frozen:
                    field.validate_default = False
                    needs_rebuild = True

            if needs_rebuild:
                try:
                    # Fix for #39:
                    # Core schema used during validation is constructed before __pydantic_init_subclass__ which means
                    # that the field.validate_default change above doesn't take effect.
                    # As a workaround, we explicitly rebuild the model to reconstruct the core schema.
                    #
                    # Downside is that unresolved forward-refs trigger an exception; for now we catch/log/ignore it.
                    # From pydantic 2.12 a new hook __pydantic_on_complete__ can be used to perform the rebuild instead.
                    # https://github.com/pydantic/pydantic/pull/11762
                    cls.model_rebuild(force=True)
                except PydanticUndefinedAnnotation as exc:
                    logger.warning(
                        "Failed to rebuild model due to undefined annotation, frozen fields may not work as expected",
                        undefined_annotation=exc.name,
                        model=cls.__name__,
                    )

    else:  # pydantic >= 2.12

        @classmethod
        def __pydantic_on_complete__(cls) -> None:
            # The default and requiredness of a field is not a property of a field
            # In the case of DisplayOnlyFieldTypes, we do kind of want that.
            # Using this method we set the right properties after the form is created
            needs_rebuild = False

            for field in cls.model_fields.values():
                if field.frozen:
                    field.validate_default = False
                    needs_rebuild = True

            if needs_rebuild:
                cls.model_rebuild(force=True)


FORMS: dict[str, Callable] = {}


def register_form(key: str, form: Callable) -> None:
    logger.info("Current Forms", forms=FORMS, new_key=key)
    if key in FORMS and form is not FORMS[key]:
        raise Exception(f"Trying to re-register form {key} with a different function")

    if not isasyncgenfunction(form) and not isgeneratorfunction(form):
        raise Exception(f"Trying to register form {key} function {form} which is not an (async) generator function")

    FORMS[key] = form


def list_forms() -> list[str]:
    return list(FORMS.keys())
