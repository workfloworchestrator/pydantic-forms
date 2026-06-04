from pydantic import Field

from pydantic_forms.core import FormPage, generate_form
from pydantic_forms.types import strEnum


def _form_schema(form_cls):
    def input_form(state):
        user_input = yield form_cls
        return user_input.model_dump()

    return generate_form(input_form, {}, [])


def test_default_factory_empty_list_is_included_in_schema():
    class Form(FormPage):
        items: list[int] = Field(default_factory=list)

    # A field using the recommended mutable-default idiom must still expose an initial value to the UI.
    assert _form_schema(Form)["properties"]["items"]["default"] == []


def test_default_factory_non_empty_is_included_in_schema():
    class Form(FormPage):
        items: list[int] = Field(default_factory=lambda: [1, 2, 3])

    assert _form_schema(Form)["properties"]["items"]["default"] == [1, 2, 3]


def test_default_factory_with_enum_values_is_serialised():
    class Color(strEnum):
        RED = "red"
        GREEN = "green"

    class Form(FormPage):
        colors: list[Color] = Field(default_factory=lambda: [Color.RED, Color.GREEN])

    assert _form_schema(Form)["properties"]["colors"]["default"] == ["red", "green"]


def test_literal_default_is_unchanged():
    class Form(FormPage):
        items: list[int] = [1, 2]

    # Literal defaults already worked; make sure the custom generator keeps them intact.
    assert _form_schema(Form)["properties"]["items"]["default"] == [1, 2]


def test_default_factory_that_raises_is_skipped():
    def boom() -> list[int]:
        raise RuntimeError("boom")

    class Form(FormPage):
        items: list[int] = Field(default_factory=boom)

    # A failing factory must never break schema generation; the field simply gets no default.
    assert "default" not in _form_schema(Form)["properties"]["items"]
