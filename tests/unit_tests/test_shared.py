import pytest
from pydantic import Field
from pydantic_core import ValidationError

from pydantic_forms.core import FormPage


def regex_field_should_be_int(field_name: str) -> str:
    # Multiline regex to match pydantic's validation error for an int field
    return rf"(?m)\n{field_name}\n\s+Input should be a valid integer"


def test_formpage_field_defaults_are_validated():
    """Test that default values in the FormPage class are validated."""

    class TestForm(FormPage):
        int_field: int = "foo"

    with pytest.raises(ValidationError, match=regex_field_should_be_int("int_field")):
        _ = TestForm().model_dump()


def test_formpage_frozen_field_default_not_validated():
    """Test that default values in the FormPage class are not validated when the field is frozen."""

    class TestForm(FormPage):
        int_field: int = Field("foo", frozen=True)

    assert TestForm().model_dump() == {"int_field": "foo"}


class TestFormWithForwardRef(FormPage):
    # Needs to be at module level for the forward-ref stuff to work
    bar_field: "Bar"
    int_field: int = "foo"


class TestFormWithForwardRefAndFrozenField(FormPage):
    # Needs to be at module level for the forward-ref stuff to work
    bar_field: "Bar"
    int_field: int = Field("foo", frozen=True)


class Bar(FormPage):
    sub_int_field: int


def test_formpage_with_forward_ref():
    """Test that default values in the FormPage class are validated when there is a forward-ref field."""
    with pytest.raises(ValidationError, match=regex_field_should_be_int("int_field")):
        _ = TestFormWithForwardRef(bar_field={"sub_int_field": 3}).model_dump()


def test_formpage_with_forward_ref_and_frozen_field():
    """Test that default values in the FormPage class are not validated when one field is frozen and another is an
    unresolved forward-ref.

    Relates to issue #39 which revealed that the way we previously changed `validate_default=False` for frozen
    fields did not work. The workaround implemented was to call `model_rebuild()` in __pydantic_init_subclass__, but the
    problem with that is it raises a PydanticUndefinedAnnotation for unresolved forward-refs.

    In that case, the FormPage should catch the exception and proceed.
    """
    assert TestFormWithForwardRefAndFrozenField(bar_field={"sub_int_field": 3}).model_dump() == {
        "bar_field": {"sub_int_field": 3},
        "int_field": "foo",
    }


def test_formpage_frozen_field_uses_default():
    """Test that default values in the FormPage class take precedence over the input value."""

    class TestForm(FormPage):
        int_field: int = Field(1, frozen=True)

    assert TestForm(int_field=2).model_dump() == {"int_field": 1}
