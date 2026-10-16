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
"""A page as a program reads it: ``readOnly`` on fields that are only shown, references inlined, the verdict as data."""

import json
from typing import Optional

import pytest
from pydantic import BaseModel, Field, model_validator

from pydantic_forms.core import FormFieldError, FormPage, Rejected, form_errors, page_schema, walk_form
from pydantic_forms.utils.schema import inline_refs
from pydantic_forms.validators import (
    Choice,
    Divider,
    Label,
    choice_list,
    migration_summary,
    read_only_field,
    read_only_list,
)


class Color(Choice):
    red = ("red", "Red")
    blue = ("blue", "Blue")


class Node(BaseModel):
    name: str
    children: list["Node"] = Field(default_factory=list)


def page():  # untyped on purpose: mypy then leaves the call-made field types alone
    class Page(FormPage):
        heading: Label
        rule: Divider
        recap: migration_summary({"labels": ["speed"], "columns": [["10G"]]})
        fixed: read_only_field("fixed")
        fixed_list: read_only_list(["a"])
        color: Color = Field(title="Colour")
        maybe: Optional[Color] = None
        colors: choice_list(Color, min_items=1)
        tree: Node
        shown: str = Field("x", frozen=True)  # any frozen field, not only the library's own types
        name: str

    return Page


Page = page()
SCHEMA = page_schema(Page, inline_refs=True)
PROPERTIES = SCHEMA["properties"]
COLOR = {"enum": ["red", "blue"], "options": {"red": "Red", "blue": "Blue"}, "type": "string"}


@pytest.mark.parametrize("name", ["heading", "rule", "recap", "fixed", "fixed_list", "shown"])
def test_a_field_that_is_shown_and_never_submitted_says_so(name):
    assert PROPERTIES[name]["readOnly"] is True


@pytest.mark.parametrize("name", ["color", "maybe", "colors", "tree", "name"])
def test_a_field_a_caller_fills_is_not_read_only(name):
    assert "readOnly" not in PROPERTIES[name]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        pytest.param("color", {**COLOR, "title": "Colour"}, id="a-choice-with-the-fields-own-title"),
        pytest.param(
            "maybe",
            {"anyOf": [COLOR | {"title": "Color"}, {"type": "null"}], "default": None},
            id="a-choice-inside-optional",
        ),
        pytest.param(
            "colors",
            {"items": COLOR | {"title": "Color"}, "minItems": 1, "title": "Colors", "type": "array"},
            id="a-list-of-choices",
        ),
    ],
)
def test_references_are_inlined_and_the_fields_own_keys_win(name, expected):
    assert PROPERTIES[name] == expected


def test_a_model_that_contains_itself_keeps_its_reference_and_its_definition():
    tree = PROPERTIES["tree"]
    assert tree["properties"]["name"] == {"title": "Name", "type": "string"}
    assert tree["properties"]["children"]["items"] == {"$ref": "#/$defs/Node"}
    assert list(SCHEMA["$defs"]) == ["Node"]
    assert SCHEMA["$defs"]["Node"]["properties"]["children"]["items"] == {"$ref": "#/$defs/Node"}
    assert "$ref" not in json.dumps({key: value for key, value in PROPERTIES.items() if key != "tree"})


def test_no_definitions_are_left_when_none_is_needed_and_the_frontends_schema_is_unchanged():
    class Picks(FormPage):
        color: Color

    assert "$defs" not in page_schema(Picks, inline_refs=True)
    assert page_schema(Picks)["properties"]["color"] == {"$ref": "#/$defs/Color"}


def test_inline_refs_follows_a_definition_that_refers_to_another_and_ignores_foreign_references():
    schema = {
        "$defs": {"A": {"properties": {"b": {"$ref": "#/$defs/B"}}, "type": "object"}, "B": {"type": "integer"}},
        "properties": {
            "a": {"$ref": "#/$defs/A", "default": None},
            "x": {"$ref": "https://example.org/B"},
        },  # foreign, though it ends in a local name
    }
    assert inline_refs(schema) == {
        "properties": {
            "a": {"properties": {"b": {"type": "integer"}}, "type": "object", "default": None},
            "x": {"$ref": "https://example.org/B"},
        }
    }


class Counted(FormPage):
    count: int

    @model_validator(mode="after")
    def not_too_many(self):
        if self.count > 10:
            raise ValueError("too many")
        return self


def one_page(state):
    yield Counted
    return state


@pytest.mark.parametrize(
    ("user_input", "expected"),
    [
        pytest.param(
            {"count": "many"},
            [
                FormFieldError(
                    loc=["count"],
                    msg="Input should be a valid integer, unable to parse string as an integer",
                    type="int_parsing",
                )
            ],
            id="a-field",
        ),
        pytest.param(
            {"count": 11}, [FormFieldError(loc=["__root__"], msg="too many", type="value_error")], id="the-page"
        ),
    ],
)
def test_the_verdict_on_a_rejected_page_as_data(user_input, expected):
    rejected = walk_form(one_page, {}, [user_input])
    assert isinstance(rejected, Rejected)
    assert form_errors(rejected.error) == expected
