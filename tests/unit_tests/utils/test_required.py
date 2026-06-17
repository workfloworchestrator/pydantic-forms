from typing import Annotated
from uuid import UUID

from annotated_types import Len, MinLen
from inline_snapshot import snapshot
from pydantic import BaseModel, Field, StringConstraints

from pydantic_forms.core import FormPage
from pydantic_forms.settings import pydantic_form_settings
from pydantic_forms.utils.required import determine_required_form_fields
from pydantic_forms.validators import (
    Accept,
    Choice,
    ContactPerson,
    DisplaySubscription,
    Divider,
    Hidden,
    Label,
    ListOfOne,
    ListOfTwo,
    Timestamp,
    callout,
    choice_list,
    migration_summary,
    read_only_field,
    read_only_list,
    unique_conlist,
)


def _default_and_extended_required(form: type[BaseModel]) -> dict[str, tuple[bool, bool]]:
    """For each field, determine the requiredness with both default and extended handling.."""
    extended = determine_required_form_fields(form)
    return {name: (field.is_required(), extended[name]) for name, field in form.model_fields.items()}


def test_required_field_handling_setting_toggles_schema_required(monkeypatch):
    """Test that the REQUIRED_FIELD_HANDLING setting is respected by the FormPage."""

    class Form(FormPage):
        no_default: int
        with_default: int = 1
        nullable_with_default: int | None = 1

    required_default = Form.model_json_schema()["required"]

    monkeypatch.setattr(pydantic_form_settings, "REQUIRED_FIELD_HANDLING", "extended")
    required_extended = Form.model_json_schema()["required"]

    assert required_default == snapshot(["no_default"])
    assert required_extended == snapshot(["no_default", "with_default"])

    # Since inline-snapshot can automatically update things wrongly: check that there is a difference
    assert required_default != required_extended

    # Assert that the required change in the schema does not make it required to be submitted
    # TODO This is my main gripe with this change.
    #  We're altering the `"required"` key in the schema for the UI to tell the user they cannot make the field empty.
    #  But if the UI simply does not submit the empty value, the backend will use the default.
    #  So for other consumers of the API, the schema will no longer reliably tell themwhich fields are required.
    #  We could consider introducing a separate key "pydantic_forms_required" in the schema so that
    #  both definitions are always available.
    assert Form(no_default=1).model_dump() == {"no_default": 1, "with_default": 1, "nullable_with_default": 1}


class FormWithAllDefaultScenarios(FormPage):
    int_no_default: int
    int_with_default: int = 1
    nullable_int_no_default: int | None  # Probably not used
    nullable_int_default_none: int | None = None
    nullable_int_with_default: int | None = 1

    list_no_default: list[int]
    list_default_factory: list[int] = Field(default_factory=list)
    list_with_default: list[int] = [1, 2, 3]
    nullable_list_no_default: list[int] | None  # Probably not used
    nullable_list_default_none: list[int] | None = None  # Probably not used

    bool_no_default: bool
    bool_with_default: bool = True
    nullable_bool_no_default: bool | None  # Probably not used
    nullable_bool_default_none: bool | None = None  # Probably not used


def test_determine_required_form_fields():
    """Test default vs. extended requiredness for all kinds of annotations."""
    assert _default_and_extended_required(FormWithAllDefaultScenarios) == snapshot(
        {
            "int_no_default": (True, True),
            "int_with_default": (False, True),
            "nullable_int_no_default": (True, True),
            "nullable_int_default_none": (False, False),
            "nullable_int_with_default": (False, False),
            "list_no_default": (True, True),
            "list_default_factory": (False, False),
            "list_with_default": (False, False),
            "nullable_list_no_default": (True, True),
            "nullable_list_default_none": (False, False),
            "bool_no_default": (True, True),
            "bool_with_default": (False, True),  # TODO discuss if we should prevent this
            "nullable_bool_no_default": (True, True),
            "nullable_bool_default_none": (False, False),
        }
    )


class FormWithDisplayOnlyFields(FormPage):
    label_with_default: Label = None
    divider_with_default: Divider = None
    hidden_with_default: Hidden = None
    label_no_default: Label
    divider_no_default: Divider
    hidden_no_default: Hidden
    callout_field: callout(message="hi")
    summary_field: migration_summary({"headers": [], "columns": []})
    display_sub: DisplaySubscription = UUID("00000000-0000-0000-0000-000000000000")
    read_only_str: read_only_field("value")
    read_only_int: read_only_field(42)
    read_only_lst: read_only_list([1, 2, 3])


def test_display_only_fields_are_never_required():
    """Test default. vs extended requiredness for display-only/immutable fields.

    None of these should ever become required.
    """
    default_and_extended = _default_and_extended_required(FormWithDisplayOnlyFields)
    assert default_and_extended == snapshot(
        {
            "label_with_default": (False, False),
            "divider_with_default": (False, False),
            "hidden_with_default": (False, False),
            "label_no_default": (False, False),
            "divider_no_default": (False, False),
            "hidden_no_default": (False, False),
            "callout_field": (False, False),
            "summary_field": (False, False),
            "display_sub": (False, False),
            "read_only_str": (False, False),
            "read_only_int": (False, False),
            "read_only_lst": (False, False),
        }
    )

    # Ensure that none of these fields ever becomes required
    assert set(default_and_extended.values()) == {(False, False)}


class FormWithListMinLengthVariants(FormPage):
    """Three equivalent ways to spell ``min_length=1``, plus a ``min_length=0`` no-op."""

    minlen1_via_field: Annotated[list[int], Field(min_length=1)] = [1, 2, 3]
    minlen0_via_field: Annotated[list[int], Field(min_length=0)] = []
    minlen1_via_last_field: Annotated[Annotated[list[int], Field(min_length=0)], Field(min_length=1)] = [1, 2, 3]
    minlen0_via_field_no_default: Annotated[list[int], Field(min_length=0)]
    minlen1_via_minlen: Annotated[list[int], MinLen(1)] = [1, 2, 3]
    minlen1_via_len: Annotated[list[int], Len(min_length=1, max_length=5)] = [1, 2, 3]


def test_list_required_only_when_min_length_positive():
    """Test default vs extended requiredness for lists dependent on min_length constraints.

    Notes:
        minlen0_via_field_no_default: Pydantic considers it required despite min_length=0. We could overrule this, but
          that would probably open another can of worms. Much easier to just set an empty list as default.

    """
    assert _default_and_extended_required(FormWithListMinLengthVariants) == snapshot(
        {
            "minlen1_via_field": (False, True),
            "minlen0_via_field": (False, False),
            "minlen1_via_last_field": (False, True),
            "minlen0_via_field_no_default": (True, True),
            "minlen1_via_minlen": (False, True),
            "minlen1_via_len": (False, True),
        }
    )


class FormWithStringConstraintVariants(FormPage):
    plain: str = "hello"
    minlen0_via_field: Annotated[str, Field(min_length=0)] = "hello"
    minlen1_via_field: Annotated[str, Field(min_length=1)] = "hello"
    minlen0_via_last_field: Annotated[Annotated[str, Field(min_length=1)], Field(min_length=0)] = "hello"
    minlen1_via_last_field: Annotated[Annotated[str, Field(min_length=0)], Field(min_length=1)] = "hello"
    minlen_via_minlen: Annotated[str, MinLen(1)] = "hello"
    pattern_rejects_empty: Annotated[str, Field(pattern=r"^.+$")] = "hello"
    pattern_via_constraints: Annotated[str, StringConstraints(pattern=r"^.+$")] = "hello"
    pattern_literal: Annotated[str, Field(pattern=r"^foo$")] = "foo"
    pattern_accepts_empty_star: Annotated[str, Field(pattern=r"^.*$")] = "hello"
    pattern_alternative_with_empty: Annotated[str, Field(pattern=r"^(foo|)$")] = "foo"
    pattern_and_minlen: Annotated[str, Field(pattern=r"^[a-z]*$", min_length=1)] = "a"


def test_string_required_only_when_constraints_reject_empty():
    """Test default vs. extended requiredness for strings dependent on min_length and pattern constraints.

    A string is required if it has a min_length>0 requirement or a regex that does not allow the empty string.
    """
    assert _default_and_extended_required(FormWithStringConstraintVariants) == snapshot(
        {
            "plain": (False, False),
            "minlen0_via_field": (False, False),
            "minlen1_via_field": (False, True),
            "minlen0_via_last_field": (False, False),
            "minlen1_via_last_field": (False, True),
            "minlen_via_minlen": (False, True),
            "pattern_rejects_empty": (False, True),
            "pattern_via_constraints": (False, True),
            "pattern_literal": (False, True),
            "pattern_accepts_empty_star": (False, False),
            "pattern_alternative_with_empty": (False, False),
            "pattern_and_minlen": (False, True),
        }
    )


class _ListItemChoice(Choice):
    A = "A"
    B = "B"


class FormWithListVariants(FormPage):
    """List-shaped components routed through the public helpers, all with defaults that satisfy their constraints."""

    list_of_one_no_default: ListOfOne[int]
    list_of_one_with_default: ListOfOne[int] = [1]
    list_of_two_no_default: ListOfTwo[int]
    list_of_two_with_default: ListOfTwo[int] = [1, 2]
    choice_list_no_min_with_default: choice_list(_ListItemChoice) = []
    choice_list_min_one_with_default: choice_list(_ListItemChoice, min_items=1) = [_ListItemChoice.A]
    unique_conlist_no_min_with_default: unique_conlist(int) = []
    unique_conlist_min_one_with_default: unique_conlist(int, min_items=1) = [1]


def test_list_helpers_required_when_min_length_positive():
    """Test default vs. extended requireness for custom list types."""
    assert _default_and_extended_required(FormWithListVariants) == snapshot(
        {
            "list_of_one_no_default": (True, True),
            "list_of_one_with_default": (False, True),
            "list_of_two_no_default": (True, True),
            "list_of_two_with_default": (False, True),
            "choice_list_no_min_with_default": (False, False),
            "choice_list_min_one_with_default": (False, True),
            "unique_conlist_no_min_with_default": (False, False),
            "unique_conlist_min_one_with_default": (False, True),
        }
    )


class _InputChoice(Choice):
    A = "A"
    B = "B"


class FormWithInputComponents(FormPage):
    accept_no_default: Accept
    choice_no_default: _InputChoice
    choice_with_default: _InputChoice = _InputChoice.A
    nullable_choice_no_default: _InputChoice | None  # Probably not used
    nullable_choice_default_none: _InputChoice | None = None
    contact_person_no_default: ContactPerson
    timestamp_no_default: Timestamp
    timestamp_with_default: Timestamp = 1700000000


def test_input_components_are_required():
    """Test default vs. extended requiredness for more complicated components."""
    assert _default_and_extended_required(FormWithInputComponents) == snapshot(
        {
            "accept_no_default": (True, True),
            "choice_no_default": (True, True),
            "choice_with_default": (False, True),
            "nullable_choice_no_default": (True, True),
            "nullable_choice_default_none": (False, False),
            "contact_person_no_default": (True, True),
            "timestamp_no_default": (True, True),
            "timestamp_with_default": (False, True),
        }
    )
