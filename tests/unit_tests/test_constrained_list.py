from pydantic import ValidationError, conlist, conset
from pytest import raises

from pydantic_forms.core import FormPage
from pydantic_forms.validators import unique_conlist


def test_constrained_list_good():
    class UniqueConListModel(FormPage):
        v: unique_conlist(int) = []

    m = UniqueConListModel(v=[1, 2, 3])
    assert m.v == [1, 2, 3]


def test_constrained_list_default():
    class UniqueConListModel(FormPage):
        v: unique_conlist(int) = []

    m = UniqueConListModel()
    assert m.v == []


class UniqueConListModel(FormPage):
    v: unique_conlist(int, min_items=1)


def test_constrained_list_ok():
    v = list(range(7))
    m = UniqueConListModel(v=v)
    assert m.v == v


def test_constrained_list_with_duplicates():
    v = [1, 1, 1]
    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=v)

    errors = exc_info.value.errors(include_url=False, include_context=False)
    expected = [{"input": v, "loc": ("v",), "msg": "List must be unique", "type": "unique_list"}]

    assert errors == expected


def test_constrained_list_invalid_value():
    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=1)

    errors = exc_info.value.errors(include_url=False, include_context=False)
    expected = [{"input": 1, "loc": ("v",), "msg": "Input should be a valid list", "type": "list_type"}]

    assert errors == expected


def test_constrained_list_invalid_type():
    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=["foo"])

    errors = exc_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "type": "int_parsing",
            "loc": ("v", 0),
            "msg": "Input should be a valid integer, unable to parse string as an integer",
            "input": "foo",
        },
    ]
    assert errors == expected


def test_constrained_list_too_short():
    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=[])

    errors = exc_info.value.errors(include_url=False, include_context=False)

    expected = [
        {
            "input": [],
            "loc": ("v",),
            "msg": "Value should have at least 1 item after validation, not 0",
            "type": "too_short",
        }
    ]

    assert errors == expected


def test_constrained_list_inherit_constraints():
    class UniqueConListModel(FormPage):
        v: unique_conlist(int, min_items=1)

    v = list(range(7))
    m = UniqueConListModel(v=v)
    assert m.v == v

    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=[1, 1, 1])

    errors = exc_info.value.errors(include_url=False, include_context=False)
    assert errors == [{"input": [1, 1, 1], "loc": ("v",), "msg": "List must be unique", "type": "unique_list"}]

    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=1)

    errors = exc_info.value.errors(include_url=False, include_context=False)
    assert errors == [{"input": 1, "loc": ("v",), "msg": "Input should be a valid list", "type": "list_type"}]

    with raises(ValidationError) as exc_info:
        UniqueConListModel(v=[])

    errors = exc_info.value.errors(include_url=False, include_context=False)

    assert errors == [
        {
            "input": [],
            "loc": ("v",),
            "msg": "Value should have at least 1 item after validation, not 0",
            "type": "too_short",
            # "ctx": {"limit_value": 1},
        }
    ]


def test_constrained_list_schema():
    class UniqueConListModel(FormPage):
        unique_conlist1: conlist(int)
        unique_conlist2: unique_conlist(int, min_items=1, max_items=3)
        unique_conlist3: conset(int)

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
