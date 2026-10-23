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
"""A field that says where its options are fetched: the ``optionsSource`` keyword, and how a page checks and lists it."""

import re
from collections.abc import Callable
from typing import Annotated, Any, Optional

import pytest
from pydantic import BaseModel, Field, PydanticInvalidForJsonSchema

from pydantic_forms.core import FormPage, page_schema
from pydantic_forms.utils.schema import options_sources
from pydantic_forms.validators import Layout, OptionsSource

LocationCode = Annotated[
    str,
    Field(json_schema_extra={"format": "locationCode"}),
    OptionsSource(url="/api/locations"),
]
LOCATION_CODE = {"format": "locationCode", "optionsSource": {"url": "/api/locations"}, "type": "string"}

CustomerId = Annotated[
    str,
    Field(json_schema_extra={"format": "customerId"}),
    OptionsSource(url="/api/customers", value="customer_id", label="{fullname} ({shortcode})"),
]

CONTACTS = OptionsSource(
    url="/api/customers/{customer}/contacts", value="email", label="name", depends_on={"customer": "1/customer"}
)
CONTACTS_SCHEMA = {
    "url": "/api/customers/{customer}/contacts",
    "value": "email",
    "label": "name",
    "dependsOn": {"customer": "1/customer"},
}


def port_id(schema: dict[str, Any]) -> None:
    """A callable ``json_schema_extra``, as a deployment may use to set the format of its own field types."""
    schema["format"] = "portId"


class Contact(BaseModel):
    name: str
    email: str


def test_a_sourced_field_keeps_its_format_and_gains_its_source():
    class Form(FormPage):
        location: LocationCode

    expected = {
        "additionalProperties": False,
        "properties": {
            "location": {
                "format": "locationCode",
                "optionsSource": {"url": "/api/locations"},
                "title": "Location",
                "type": "string",
            }
        },
        "required": ["location"],
        "title": "unknown",
        "type": "object",
    }
    assert page_schema(Form) == expected


def test_every_key_is_emitted_in_camel_case_and_unset_ones_are_left_out():
    class Form(FormPage):
        location: LocationCode
        node: Annotated[
            int,
            OptionsSource(
                url="/api/locations/{location}/nodes?status=active",
                search="q",
                items="/data/nodes",
                value="id",
                label="{name} ({status})",
                depends_on={"location": "1/location"},
            ),
        ]

    assert page_schema(Form)["properties"]["node"]["optionsSource"] == {
        "url": "/api/locations/{location}/nodes?status=active",
        "search": "q",
        "items": "/data/nodes",
        "value": "id",
        "label": "{name} ({status})",
        "dependsOn": {"location": "1/location"},
    }


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        pytest.param(
            Annotated[int, Field(json_schema_extra=port_id), OptionsSource(url="/api/nodes/7/ports")],
            {"format": "portId", "optionsSource": {"url": "/api/nodes/7/ports"}, "type": "integer"},
            id="a-callable-json-schema-extra",
        ),
        pytest.param(Annotated[LocationCode, Layout(span=6)], LOCATION_CODE | {"layout": {"span": 6}}, id="a-layout"),
        pytest.param(
            Annotated[LocationCode, Field(description="Where the service lands")],
            LOCATION_CODE | {"description": "Where the service lands"},
            id="a-fields-own-keys",
        ),
    ],
)
def test_the_source_composes_with_what_the_field_already_carries(field_type, expected):
    class Form(FormPage):
        field: field_type

    assert page_schema(Form)["properties"]["field"] == expected | {"title": "Field"}


def test_a_list_field_describes_the_options_of_its_items():
    class Form(FormPage):
        codes: Annotated[list[str], OptionsSource(url="/api/locations")]

    assert page_schema(Form)["properties"]["codes"] == {
        "items": {"type": "string"},
        "optionsSource": {"url": "/api/locations"},
        "title": "Codes",
        "type": "array",
    }


def test_a_nested_type_keeps_its_source_beside_the_reference_and_after_inlining():
    class Form(FormPage):
        customer: CustomerId
        contact: Annotated[Contact, CONTACTS]

    assert page_schema(Form)["properties"]["contact"] == {"$ref": "#/$defs/Contact", "optionsSource": CONTACTS_SCHEMA}
    inlined = page_schema(Form, inline_refs=True)["properties"]["contact"]
    assert inlined["optionsSource"] == CONTACTS_SCHEMA
    assert inlined["properties"]["email"] == {"title": "Email", "type": "string"}


def sourced_page():  # untyped on purpose: mypy then leaves the call-made field types alone
    class Form(FormPage):
        customer: CustomerId
        contact: Annotated[str, CONTACTS]
        codes: list[LocationCode]
        maybe: Optional[LocationCode] = None
        name: str

    return Form


@pytest.mark.parametrize("inline", [False, True], ids=["as-the-frontend-gets-it", "inlined"])
def test_options_sources_lists_the_sourced_fields_by_location_wherever_the_keyword_sits(inline):
    schema = page_schema(sourced_page(), inline_refs=inline)
    assert options_sources(schema) == {
        "/properties/customer": {
            "url": "/api/customers",
            "value": "customer_id",
            "label": "{fullname} ({shortcode})",
        },
        "/properties/contact": CONTACTS_SCHEMA,
        "/properties/codes/items": {"url": "/api/locations"},
        "/properties/maybe/anyOf/0": {"url": "/api/locations"},
    }


def test_a_list_of_a_sourced_type_carries_the_source_on_its_items():
    properties = page_schema(sourced_page())["properties"]
    assert properties["codes"]["items"]["optionsSource"] == {"url": "/api/locations"}
    assert "optionsSource" not in properties["codes"]
    assert properties["maybe"]["anyOf"][0]["optionsSource"] == {"url": "/api/locations"}


class Port(BaseModel):
    node: Annotated[int, OptionsSource(url="/api/nodes")]
    port: Annotated[
        int,
        OptionsSource(
            url="/api/nodes/{node}/ports?speed={speed}", depends_on={"node": "1/node", "speed": "/service_speed"}
        ),
    ]


class PortsForm(FormPage):
    service_speed: int
    ports: list[Port]


def test_the_fields_of_nested_models_and_list_items_are_listed_at_their_location():
    assert list(options_sources(page_schema(PortsForm))) == [
        "/properties/ports/items/properties/node",
        "/properties/ports/items/properties/port",
    ]


def test_a_pointer_may_go_up_to_a_row_sibling_or_to_the_page():
    assert page_schema(PortsForm)["properties"]["ports"]["items"] == {"$ref": "#/$defs/Port"}
    port = page_schema(PortsForm, inline_refs=True)["properties"]["ports"]["items"]["properties"]["port"]
    assert port["optionsSource"]["dependsOn"] == {"node": "1/node", "speed": "/service_speed"}


@pytest.mark.parametrize(
    "pointer",
    [
        pytest.param("/service_speed", id="from-the-page"),
        pytest.param("3/service_speed", id="up-through-the-row-and-the-list"),
        pytest.param("1/node", id="a-row-sibling"),
        pytest.param("/ports/0/node", id="into-a-list-by-index"),
        pytest.param("/ports/-/node", id="into-a-list-by-dash"),
    ],
)
def test_a_pointer_that_reaches_a_field_is_accepted(pointer):
    class Row(BaseModel):
        node: int
        port: Annotated[int, OptionsSource(url="/api/ports?by={x}", depends_on={"x": pointer})]

    class Form(FormPage):
        service_speed: int
        ports: list[Row]

    assert "/properties/ports/items/properties/port" in options_sources(page_schema(Form))


@pytest.mark.parametrize(
    "pointer",
    [
        pytest.param("1/speed", id="a-name-the-row-does-not-have"),
        pytest.param("2/service_speed", id="the-list-not-the-page"),
        pytest.param("4/service_speed", id="above-the-page"),
        pytest.param("/speed", id="a-name-the-page-does-not-have"),
        pytest.param("/ports/node", id="a-name-where-an-index-is-due"),
    ],
)
def test_a_pointer_that_reaches_no_field_is_refused_as_the_page_is_defined(pointer):
    class Row(BaseModel):
        node: int
        port: Annotated[int, OptionsSource(url="/api/ports?by={x}", depends_on={"x": pointer})]

    expected = f"Form: /properties/ports/items/properties/port fills 'x' from '{pointer}', which points at no field"
    with pytest.raises(ValueError, match=re.escape(expected)):

        class Form(FormPage):
            service_speed: int
            ports: list[Row]


def test_a_page_that_is_a_plain_model_is_refused_when_its_schema_is_made():
    class Page(BaseModel):  # a generator may yield any model; it has no hook, so page_schema is where it is checked
        contact: Annotated[str, OptionsSource(url="/api/customers/{c}/contacts", depends_on={"c": "1/customer"})]

    with pytest.raises(
        ValueError, match="Page: /properties/contact fills 'c' from '1/customer', which points at no field"
    ):
        page_schema(Page)


def test_a_page_whose_schema_cannot_be_made_yet_is_left_for_page_schema():
    class Incomplete(FormPage):  # a forward reference that never resolves: defining the page must still work
        rows: list["Missing"]  # noqa: F821

    class Arbitrary(FormPage):  # a type without a JSON schema: the failure stays where it is today
        callback: Callable[[], int]
        location: LocationCode

    with pytest.raises(PydanticInvalidForJsonSchema):
        page_schema(Arbitrary)


def test_a_pointer_looks_through_an_optional_nested_model():
    class Row(BaseModel):
        node: int

    class Form(FormPage):
        row: Optional[Row] = None
        port: Annotated[int, OptionsSource(url="/api/ports?node={node}", depends_on={"node": "/row/node"})]

    assert "/properties/port" in options_sources(page_schema(Form))


def test_a_model_that_contains_itself_lists_each_field_once():
    class Tree(BaseModel):
        name: Annotated[str, OptionsSource(url="/api/names")]
        children: list["Tree"] = Field(default_factory=list)

    class Form(FormPage):
        tree: Tree

    assert list(options_sources(page_schema(Form))) == ["/properties/tree/properties/name"]


@pytest.mark.parametrize(
    ("pointer", "accepted"),
    [
        pytest.param("/customerId", True, id="the-name-in-the-schema"),
        pytest.param("/customer", False, id="the-python-name-of-an-aliased-field"),
    ],
)
def test_a_pointer_names_the_field_as_the_schema_does(pointer, accepted):
    def page():
        class Form(FormPage):
            customer: CustomerId = Field(alias="customerId")
            contact: Annotated[str, OptionsSource(url="/api/customers/{c}/contacts", depends_on={"c": pointer})]

        return Form

    if accepted:
        assert options_sources(page_schema(page()))["/properties/contact"]["dependsOn"] == {"c": pointer}
    else:
        with pytest.raises(ValueError, match="/properties/contact fills 'c'"):
            page()


def test_the_source_does_not_change_validation():
    class Form(FormPage):
        location: LocationCode
        codes: Annotated[list[str], OptionsSource(url="/api/locations")] = []

    assert Form(location="AMS001", codes=["UTR001"]).model_dump() == {"location": "AMS001", "codes": ["UTR001"]}


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        pytest.param({"url": ""}, "url must not be empty", id="an-empty-url"),
        pytest.param(
            {"url": "/a/{b}"}, r"url names \['b'\], which depends_on does not map", id="a-placeholder-in-the-path"
        ),
        pytest.param({"url": "/a?b={c}"}, r"url names \['c'\]", id="a-placeholder-in-the-query-string"),
        pytest.param(
            {"url": "/a/{b}", "depends_on": {"c": "1/c"}},
            r"url names \['b'\]",
            id="a-placeholder-mapped-under-another-name",
        ),
        pytest.param(
            {"url": "/a", "depends_on": {"b": "1/b"}},
            r"depends_on maps \['b'\], which url does not name",
            id="a-pointer-the-url-does-not-use",
        ),
        pytest.param({"url": "/a/{b}", "depends_on": {"b": "b"}}, "is not a JSON pointer", id="a-bare-name"),
        pytest.param(
            {"url": "/a/{b}", "depends_on": {"b": "a/b"}}, "is not a JSON pointer", id="a-path-without-a-level"
        ),
        pytest.param({"url": "/a/{b}", "depends_on": {"b": "-1/b"}}, "is not a JSON pointer", id="a-negative-level"),
        pytest.param({"url": "/a/{b}", "depends_on": {"b": "1#"}}, "is not a JSON pointer", id="the-name-form"),
        pytest.param({"url": "/a/{b}", "depends_on": {"b": ""}}, "is not a JSON pointer", id="an-empty-pointer"),
        pytest.param({"url": "/a", "items": "data"}, "items must be a JSON pointer", id="items-that-is-no-pointer"),
    ],
)
def test_a_source_that_cannot_be_followed_is_refused_when_declared(kwargs, message):
    with pytest.raises(ValueError, match=message):
        OptionsSource(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param({"url": "/a/{b}", "depends_on": {"b": "1/b"}}, id="a-row-sibling"),
        pytest.param({"url": "/a?s=1&s=2&b={c}", "depends_on": {"c": "/c"}}, id="a-query-string-as-the-route-reads-it"),
        pytest.param({"url": "/a/{b}", "depends_on": {"b": "0/b"}}, id="into-the-fields-own-value"),
        pytest.param({"url": "/a/{b}", "depends_on": {"b": "12/a/b"}}, id="many-levels-up"),
        pytest.param({"url": "/a/{b}", "depends_on": {"b": "/x~1y/b"}}, id="an-escaped-slash"),
        pytest.param({"url": "/a", "items": "/data/items"}, id="a-json-pointer-into-the-response"),
        pytest.param({"url": "https://crm.example.org/customers"}, id="an-absolute-url"),
        pytest.param({"url": "/a", "label": "{name} ({code})"}, id="a-label-template-names-item-keys-not-fields"),
    ],
)
def test_a_source_that_can_be_followed_is_accepted(kwargs):
    OptionsSource(**kwargs)
