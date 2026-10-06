from typing import Annotated

import pytest
from pydantic import BaseModel, Field

from pydantic_forms.core import FormPage
from pydantic_forms.validators import Layout, LongText


def test_layout_json_schema_leaves_out_unset_options():
    class Form(FormPage):
        name: Annotated[str, Layout(span=6, new_row=True, align="end")]
        city: Annotated[str, Layout(start=4)]
        full: Annotated[str, Layout()]
        tall: Annotated[str, Layout(span=6, row_span=2)]

    properties = Form.model_json_schema()["properties"]
    assert properties["name"]["layout"] == {"span": 6, "newRow": True, "align": "end"}
    assert properties["city"]["layout"] == {"start": 4}
    assert "layout" not in properties["full"]
    assert properties["tall"]["layout"] == {"span": 6, "rowSpan": 2}


def test_layout_combines_with_other_schema_extras():
    class Form(FormPage):
        comments: Annotated[LongText, Layout(span=6)] = Field(title="Comments")

    assert Form.model_json_schema()["properties"]["comments"] == {
        "format": "long",
        "layout": {"span": 6},
        "title": "Comments",
        "type": "string",
    }


def test_layout_in_nested_model():
    class Address(BaseModel):
        street: Annotated[str, Layout(span=8)]
        postal_code: Annotated[str, Layout(span=4)]

    class Form(FormPage):
        address: Address

    properties = Form.model_json_schema()["$defs"]["Address"]["properties"]
    assert properties["street"]["layout"] == {"span": 8}
    assert properties["postal_code"]["layout"] == {"span": 4}


def test_layout_does_not_affect_validation():
    class Form(FormPage):
        name: Annotated[str, Layout(span=6)]

    assert Form(name="Jane").model_dump() == {"name": "Jane"}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"span": 0},
        {"span": 13},
        {"start": 0},
        {"start": 13},
        {"start": 10, "span": 6},
        {"start": 12, "span": 2},
        {"row_span": 0},
    ],
)
def test_layout_rejects_positions_outside_the_grid(kwargs):
    with pytest.raises(ValueError):
        Layout(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"span": 1},
        {"span": 12},
        {"start": 12},
        {"start": 7, "span": 6},
        {"start": 1, "span": 12},
        {"row_span": 3},
    ],
)
def test_layout_accepts_positions_within_the_grid(kwargs):
    Layout(**kwargs)
