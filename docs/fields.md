# Field types

All field types are exported from `pydantic_forms.validators`.

## Display-only

These fields are `frozen` and don't collect input; they only affect how the form is rendered.

| Field | Description |
|---|---|
| `Label` | A plain text line. |
| `Divider` | A visual separator line. |
| `Hidden` | A field that isn't shown to the user. |
| `Callout` (`callout(header=, message=, icon_type=, message_type=)`) | An info/success/warning/danger callout box. |
| `Markdown` (`markdown(content=, color=)`) | A block of rendered Markdown. |
| `MigrationSummary` (`migration_summary(data)`) | A static table, built from a `{headers, labels, columns}` dict. |
| `DisplaySubscription` | Displays a subscription by UUID. Deprecated in favor of `orchestrator.forms.validators.DisplaySubscription`. |

## Basic input

| Field | Description |
|---|---|
| `str` | Plain single-line text input. |
| `LongText` | Multi-line text input. |
| `int`, `float`, `bool` | Number and checkbox inputs. |
| `Accept` | A checklist the user must fully accept before the value is considered `"ACCEPTED"`. |
| `timestamp(show_time_select=, min=, max=, ...)` / `Timestamp` | A date/time picker, backed by an `int` (unix timestamp). |
| `OrganisationId` | A `str` tagged for organisation-ID rendering. Deprecated in favor of `orchestrator.forms.validators.CustomerId`. |

## Choices

| Field | Description |
|---|---|
| `Choice` | A `str` enum where each member is `(value, label)`, so the displayed label can differ from the stored value. |
| `choice_list(item_type, min_items=, max_items=, unique_items=)` | A multi-select list of `Choice` values. |

## Lists

| Field | Description |
|---|---|
| `ListOfOne[T]` | A list constrained to exactly one item. |
| `ListOfTwo[T]` | A list constrained to exactly two distinct items. |
| `unique_conlist(item_type, min_items=, max_items=)` | A list of unique items of a given type. |
| `read_only_list(default)` | A list fixed to `default` and rendered as disabled. |

## Contact persons

| Field | Description |
|---|---|
| `ContactPerson` | A model with `name`, `email` (validated) and `phone`. |
| `contact_person_list(organisation=, min_items=, max_items=)` | A list of `ContactPerson`. Deprecated in favor of `orchestrator.forms.validators.customer_contact_list`. |

## Read-only

| Field | Description |
|---|---|
| `read_only_field(default, merge_type=)` | A scalar field fixed to `default`, rendered as disabled. Supports `str`, `int`, `float`, `bool`, `None`, enums and `UUID`. |
