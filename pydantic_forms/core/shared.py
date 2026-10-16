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
from dataclasses import dataclass
from inspect import isasyncgenfunction, isgeneratorfunction
from typing import Any, Callable, ClassVar, Union, cast

import structlog
from pydantic import BaseModel, ConfigDict, Field, PydanticUndefinedAnnotation, ValidationError, version
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from pydantic_core import core_schema
from pydantic_i18n import PydanticI18n

from pydantic_forms.core.translations import translations
from pydantic_forms.exceptions import FormValidationError
from pydantic_forms.types import FormMeta, InputForm, State
from pydantic_forms.utils import schema as schema_utils
from pydantic_forms.validators.components.buttons import merge_buttons_into_meta

logger = structlog.get_logger(__name__)


PYDANTIC_VERSION = version.version_short()


class GenerateFormJsonSchema(GenerateJsonSchema):
    """JSON schema generator that also emits ``default`` values produced by ``default_factory``.

    Pydantic intentionally leaves ``default_factory`` results out of the generated JSON schema. For
    forms this is a problem: ``default_factory`` is the recommended way to declare mutable defaults
    (``Field(default_factory=list)`` and friends), and frontends pre-fill fields from the schema
    ``default``. Without it such fields render uninitialised, and dynamic array/object widgets reject
    submission until the user performs a dummy add/remove interaction to materialise an empty value.

    This generator evaluates argument-less factories and adds their result as the schema ``default``.
    Factories that need the already-validated data (``default_factory_takes_data``) cannot be
    evaluated at schema-generation time and are skipped, as is any factory that raises.
    """

    def default_schema(self, schema: core_schema.WithDefaultSchema) -> JsonSchemaValue:
        json_schema = super().default_schema(schema)
        if (
            "default" not in json_schema
            and "default_factory" in schema
            and not schema.get("default_factory_takes_data", False)
        ):
            factory = cast(Callable[[], Any], schema["default_factory"])
            try:
                json_schema["default"] = self.encode_default(factory())
            except Exception:  # never let a factory break schema generation
                logger.debug("Could not evaluate default_factory for form schema", exc_info=True)
        return json_schema


class DisplayOnlyFieldType:
    pass


class FormPage(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        title="unknown",
        extra="forbid",
        validate_default=True,
    )

    meta__: ClassVar[FormMeta | None] = None
    """Data about the page itself, passed to the frontend alongside its JSON schema.

    Set it on a subclass to tell the frontend something the schema cannot express, such as whether
    another page follows (`hasNext`). It travels out as the `meta` key of the `FormNotCompleteError`
    response, see `form_meta()`. Being a `ClassVar` it is not a form field, so it stays out of the
    schema and the validated result.

    Relabel or restyle the previous/next buttons with a `ButtonsConfig` field, or else with
    `customButtons` here. The two can't be combined.
    """

    def __init__(self, **data: Any):
        frozen_fields = {k: v for k, v in self.__class__.model_fields.items() if v.frozen}

        def get_value(k: str, v: Any) -> Any:
            if k in frozen_fields:
                return frozen_fields[k].default
            return v

        mutable_data = {k: get_value(k, v) for k, v in data.items()}
        super().__init__(**mutable_data)

    @classmethod
    def form_meta(cls) -> FormMeta | None:
        """Return `meta__` with the page's `ButtonsConfig` field added."""
        return merge_buttons_into_meta(cls.__name__, cls.meta__, cls.model_fields)

    if PYDANTIC_VERSION in ("2.9", "2.10", "2.11"):

        @classmethod
        def __pydantic_init_subclass__(cls, /, **kwargs: Any) -> None:
            # The default and requiredness of a field is not a property of a field
            # In the case of DisplayOnlyFieldTypes, we do kind of want that.
            # Using this method we set the right properties after the form is created
            cls.form_meta()  # run now so a conflicting declaration fails on import, not when the page is first sent
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
            cls.form_meta()
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


def get_form_meta(form: type[BaseModel]) -> Any:
    """Return the meta to send to the frontend with `form`.

    A generator may yield any pydantic model, not only a `FormPage`; such a model can still carry a `meta__`.
    """
    if issubclass(form, FormPage):
        return form.form_meta()
    return getattr(form, "meta__", None)


@dataclass(frozen=True)
class NextPage:
    """The form asks for another page: its model, and its index (the number of pages accepted before it)."""

    model: InputForm
    index: int


@dataclass(frozen=True)
class Complete:
    """Every page was accepted: the result of the form."""

    state: State


@dataclass(frozen=True)
class Rejected:
    """A page did not validate: which one, its model, and the verdict."""

    model: InputForm
    index: int
    error: FormValidationError


# The three endings of ``walk_form``.
WalkOutcome = Union[NextPage, Complete, Rejected]


def validation_error(page: InputForm, error: ValidationError, locale: str = "en_US") -> FormValidationError:
    """The verdict on a page that did not validate, its messages translated."""
    verdict = FormValidationError(page.__name__, error, PydanticI18n(translations), locale)
    verdict.__cause__ = error  # as ``raise ... from error`` would chain it
    return verdict


def page_schema(page: type[BaseModel], *, inline_refs: bool = False) -> JsonSchemaValue:
    """The JSON schema of a page.

    A frozen field of the page is marked ``readOnly``: the page sets its value itself and ignores anything submitted
    for it. A frozen field of a nested model is regular input and carries no marker.

    With ``inline_refs`` every ``$ref`` to a ``$defs`` entry is replaced by that entry, so a program gets one
    self-contained document per page; see ``pydantic_forms.utils.schema.inline_refs``.
    """
    schema = page.model_json_schema(schema_generator=GenerateFormJsonSchema)
    properties = schema.get("properties", {})
    frozen = (field.alias or name for name, field in page.model_fields.items() if field.frozen)
    for key in filter(properties.__contains__, frozen):
        properties[key]["readOnly"] = True
    return schema_utils.inline_refs(schema) if inline_refs else schema


class FormFieldError(BaseModel):
    """One message of the verdict on a rejected page, as data."""

    loc: list[Union[int, str]] = Field(
        description="Path of the rejected value on the page: the field name, then an index or a sub-field. "
        '``["__root__"]`` for a page-level error.'
    )
    msg: str = Field(description="The translated validation error.")
    type: str = Field(description='pydantic\'s error type, e.g. "missing", "enum", "value_error".')


def form_errors(error: FormValidationError) -> list[FormFieldError]:
    """The verdict on a rejected page as data: one ``FormFieldError`` per message."""
    return [FormFieldError(loc=list(e["loc"]), msg=e["msg"], type=e["type"]) for e in error.errors]
