import pytest
from pydantic import Field
from pydantic_core import ValidationError

from pydantic_forms.core import FormPage


def test_formpage_field_defaults_are_validated():
    """Test that default values in the FormPage class are validated."""

    class TestForm(FormPage):
        x: int = "foo"

    with pytest.raises(ValidationError):
        _ = TestForm().model_dump()


def test_formpage_frozen_field_default_not_validated():
    """Test that default values in the FormPage class are not validated when the field is frozen."""

    class TestForm(FormPage):
        x: int = Field("foo", frozen=True)

    assert TestForm().model_dump() == {"x": "foo"}


def test_formpage_frozen_field_uses_default():
    """Test that default values in the FormPage class take precedence over the input value."""

    class TestForm(FormPage):
        x: int = Field(1, frozen=True)

    assert TestForm(x=2).model_dump() == {"x": 1}
