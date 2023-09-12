from typing import TypeVar

from pydantic import ValidationError
from pytest import raises

from pydantic_forms.core import FormPage
from pydantic_forms.validators import UniqueConstrainedList, unique_conlist


def test_constrained_list_good():
    class UniqueConListModel(FormPage):
        v: unique_conlist(int, unique_items=True) = []

    m = UniqueConListModel(v=[1, 2, 3])
    assert m.v == [1, 2, 3]


def test_constrained_list_default():
    class UniqueConListModel(FormPage):
        v: unique_conlist(int, unique_items=True) = []

    m = UniqueConListModel()
    assert m.v == []


class UniqueConListModel(FormPage):
    v: unique_conlist(int, min_items=1, unique_items=True)


def test_constrained_list_ok():
    v = list(range(7))
    m = UniqueConListModel(v=v)
    assert m.v == v


def test_constrained_list_with_duplicates():
    v = [1, 1, 1]
    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=v)

    errors = exc_info.value.errors(include_url=False, include_context=False)
    expected = [{"input": v, "loc": ("v",), "msg": "Value error, Items must be unique", "type": "value_error"}]

    assert errors == expected


def test_constrained_list_invalid_value():
    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=1)

    errors = exc_info.value.errors(include_url=False, include_context=False)
    expected = [{"input": 1, "loc": ("v",), "msg": "Input should be a valid list", "type": "list_type"}]

    assert errors == expected


def test_constrained_list_too_short():
    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=[])

    errors = exc_info.value.errors(include_url=False, include_context=False)

    expected = [
        {
            # "ctx": {"error": ListMinLengthError(limit_value=1)},
            "input": [],
            "loc": ("v",),
            "msg": "Value error, ensure this value has at least 1 items",
            "type": "value_error",
        }
    ]

    assert errors == expected


def test_constrained_list_inherit_constraints():
    T = TypeVar("T")

    class Parent(UniqueConstrainedList[T]):
        min_items = 1

    class Child(Parent[T]):
        unique_items = True

    class UniqueConListModel(FormPage):
        v: Child[int]

    v = list(range(7))
    m = UniqueConListModel(v=v)
    assert m.v == v

    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=[1, 1, 1])
    assert exc_info.value.errors() == [
        {"loc": ("v",), "msg": "the list has duplicated items", "type": "value_error.list.unique_items"}
    ]

    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=1)
    assert exc_info.value.errors() == [{"loc": ("v",), "msg": "value is not a valid list", "type": "type_error.list"}]

    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=[])
    assert exc_info.value.errors() == [
        {
            "loc": ("v",),
            "msg": "ensure this value has at least 1 items",
            "type": "value_error.list.min_items",
            "ctx": {"limit_value": 1},
        }
    ]


def test_constrained_list_schema():
    class UniqueConListClass(UniqueConstrainedList[int]):
        min_items = 1
        max_items = 3
        unique_items = True

    class UniqueConListModel(FormPage):
        unique_conlist1: unique_conlist(int)
        unique_conlist2: unique_conlist(int, min_items=1, max_items=3, unique_items=True)
        unique_conlist3: UniqueConListClass

    expected = {
        "additionalProperties": False,
        "properties": {
            "unique_conlist1": {"items": {"type": "integer"}, "title": "Unique Conlist1", "type": "array"},
            "unique_conlist2": {
                "items": {"type": "integer"},
                "maxItems": 3,
                "minItems": 1,
                "title": "Unique Conlist2",
                "type": "array",
                "uniqueItems": True,
            },
            "unique_conlist3": {
                "items": {"type": "integer"},
                "maxItems": 3,
                "minItems": 1,
                "title": "Unique Conlist3",
                "type": "array",
                "uniqueItems": True,
            },
        },
        "required": ["unique_conlist1", "unique_conlist2", "unique_conlist3"],
        "title": "unknown",
        "type": "object",
    }
    assert UniqueConListModel.model_json_schema() == expected
