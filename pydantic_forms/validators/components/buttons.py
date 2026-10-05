# Copyright 2019-2026 SURF.
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
from dataclasses import asdict, dataclass
from typing import Any, Optional, cast

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.fields import FieldInfo
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import PydanticOmit, core_schema

from pydantic_forms.types import ButtonConfig, CustomButtons, FormMeta


@dataclass(frozen=True)
class Button:
    """Label and/or color for one button. Left as `None`, the frontend keeps its default."""

    text: Optional[str] = None
    color: Optional[str] = None

    def to_meta(self) -> ButtonConfig:
        return cast(ButtonConfig, {key: value for key, value in asdict(self).items() if value is not None})


@dataclass(frozen=True)
class ButtonsConfig:
    """Overrides for the previous/next buttons, set as the default of a form field.

    `custom_buttons: ButtonsConfig = ButtonsConfig(next=Button(text="Confirm"))` sends the overrides to the
    frontend as `customButtons` in the page's meta. The field takes no input and stays out of the schema and
    the validated result. It can't be combined with `customButtons` in the page's `meta__`.
    """

    previous: Optional[Button] = None
    next: Optional[Button] = None

    def to_meta(self) -> CustomButtons:
        buttons = {"previous": self.previous, "next": self.next}
        return cast(CustomButtons, {name: button.to_meta() for name, button in buttons.items() if button is not None})

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        # Display-only: any input is dropped. The config is read from the field's default by `FormPage.form_meta()`.
        return core_schema.no_info_plain_validator_function(lambda _: None)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        raise PydanticOmit


def merge_buttons_into_meta(
    form_name: str, meta: Optional[FormMeta], fields: dict[str, FieldInfo]
) -> Optional[FormMeta]:
    """Return `meta` with the `ButtonsConfig` default among `fields` set as its `customButtons`.

    `meta` itself is never modified, and is returned as-is when no field is a `ButtonsConfig`.
    """
    buttons_fields = {name: field for name, field in fields.items() if field.annotation is ButtonsConfig}
    if not buttons_fields:
        return meta
    if missing := [name for name, field in buttons_fields.items() if not isinstance(field.default, ButtonsConfig)]:
        raise TypeError(f"{form_name}.{missing[0]} needs a ButtonsConfig(...) default")
    if len(buttons_fields) > 1:
        raise TypeError(f"{form_name} has more than one ButtonsConfig field; declare all buttons in a single one")
    if meta and "customButtons" in meta:
        raise TypeError(
            f"{form_name} declares its buttons both in meta__['customButtons'] and in a ButtonsConfig field"
        )

    (field,) = buttons_fields.values()
    return {**(meta or {}), "customButtons": field.default.to_meta()}
