from pydantic import ConfigDict
from pytest import raises

from pydantic_forms.core import FormPage
from pydantic_forms.core.asynchronous import generate_form, post_form
from pydantic_forms.exceptions import FormNotCompleteError, FormOverflowError, FormValidationError
from pydantic_forms.types import strEnum

# TODO: Remove when generic forms of pydantic_forms are ready
from pydantic_forms.utils.json import json_dumps, json_loads


class TestChoices(strEnum):
    A = "a"
    B = "b"


class TestForm(FormPage):
    generic_select: TestChoices


async def test_post_process_yield():
    async def input_form(state):
        user_input = yield TestForm
        yield user_input.model_dump() | {"extra": 234}

    validated_data = await post_form(input_form, {"previous": True}, [{"generic_select": "a"}])

    expected = {"generic_select": "a", "extra": 234}
    assert json_loads(json_dumps(validated_data)) == expected


async def test_post_process_extra_data():
    async def input_form(state):
        user_input = yield TestForm
        yield user_input.model_dump() | {"extra": 234}

    with raises(FormValidationError) as e:
        await post_form(input_form, {"previous": True}, [{"generic_select": "a", "extra_data": False}])

    expected = "1 validation error for TestForm\nextra_data\n  Extra inputs are not permitted (type=extra_forbidden)"
    assert str(e.value) == expected


async def test_post_process_validation_errors():
    async def input_form(state):
        user_input = yield TestForm
        yield user_input.dict()

    with raises(FormValidationError) as e:
        await post_form(input_form, {}, [{"generic_select": 1, "extra_data": False}])

    expected = "2 validation errors for TestForm\ngeneric_select\n  Input should be 'a' or 'b' (type=enum; expected='a' or 'b')\nextra_data\n  Extra inputs are not permitted (type=extra_forbidden)"
    assert str(e.value) == expected

    with raises(FormValidationError) as e:
        await post_form(input_form, {}, [{"generic_select": "c"}])

    expected = (
        "1 validation error for TestForm\ngeneric_select\n  Input should be 'a' or 'b' (type=enum; expected='a' or 'b')"
    )
    assert str(e.value) == expected


async def test_post_form_wizard():
    # Return if there is no form
    assert (await post_form(None, {}, [])) == {}
    assert (await post_form([], {}, [])) == {}

    async def input_form(state):
        class TestForm1(FormPage):
            model_config = ConfigDict(title="Some title")

            generic_select1: TestChoices

        class TestForm2(FormPage):
            generic_select2: TestChoices

        class TestForm3(FormPage):
            generic_select3: TestChoices

        user_input_1 = yield TestForm1

        if user_input_1.generic_select1 == TestChoices.A:
            user_input_2 = yield TestForm2
        else:
            user_input_2 = yield TestForm3

        yield {**user_input_1.model_dump(), **user_input_2.model_dump()}

    # Submit 1
    with raises(FormNotCompleteError) as error_info:
        await post_form(input_form, {"previous": True}, [])

    assert error_info.value.form == {
        "title": "Some title",
        "type": "object",
        "additionalProperties": False,
        "$defs": {
            "TestChoices": {
                "enum": ["a", "b"],
                "title": "TestChoices",
                "type": "string",
            }
        },
        "properties": {"generic_select1": {"$ref": "#/$defs/TestChoices"}},
        "required": ["generic_select1"],
    }

    # Submit 2
    with raises(FormNotCompleteError) as error_info:
        await post_form(input_form, {"previous": True}, [{"generic_select1": "b"}])

    assert error_info.value.form == {
        "title": "unknown",
        "type": "object",
        "additionalProperties": False,
        "$defs": {
            "TestChoices": {
                "enum": ["a", "b"],
                "title": "TestChoices",
                "type": "string",
            }
        },
        "properties": {"generic_select3": {"$ref": "#/$defs/TestChoices"}},
        "required": ["generic_select3"],
    }

    # Submit complete
    validated_data = await post_form(
        input_form, {"previous": True}, [{"generic_select1": "b"}, {"generic_select3": "a"}]
    )

    expected = {"generic_select1": "b", "generic_select3": "a"}
    assert expected == json_loads(json_dumps(validated_data))

    # Submit overcomplete
    with raises(FormOverflowError, match="1 remaining"):
        await post_form(
            input_form, {"previous": True}, [{"generic_select1": "b"}, {"generic_select3": "a"}, {"to_much": True}]
        )


async def test_generate_form():
    async def input_form(state):
        class TestForm1(FormPage):
            model_config = ConfigDict(title="Some title")

            generic_select1: TestChoices

        class TestForm2(FormPage):
            generic_select2: TestChoices

        class TestForm3(FormPage):
            generic_select3: TestChoices

        user_input_1 = yield TestForm1

        if user_input_1.generic_select1 == TestChoices.A:
            user_input_2 = yield TestForm2
        else:
            user_input_2 = yield TestForm3

        yield {**user_input_1.model_dump(), **user_input_2.model_dump()}

    # Submit 1
    form = await generate_form(input_form, {"previous": True}, [])

    assert form == {
        "title": "Some title",
        "type": "object",
        "additionalProperties": False,
        "$defs": {
            "TestChoices": {
                "enum": ["a", "b"],
                "title": "TestChoices",
                "type": "string",
            }
        },
        "properties": {"generic_select1": {"$ref": "#/$defs/TestChoices"}},
        "required": ["generic_select1"],
    }

    # Submit 2
    form = await generate_form(input_form, {"previous": True}, [{"generic_select1": "b"}])

    assert form == {
        "title": "unknown",
        "type": "object",
        "additionalProperties": False,
        "$defs": {
            "TestChoices": {
                "enum": ["a", "b"],
                "title": "TestChoices",
                "type": "string",
            }
        },
        "properties": {"generic_select3": {"$ref": "#/$defs/TestChoices"}},
        "required": ["generic_select3"],
    }

    # Submit complete
    form = await generate_form(input_form, {"previous": True}, [{"generic_select1": "b"}, {"generic_select3": "a"}])
    assert form is None
