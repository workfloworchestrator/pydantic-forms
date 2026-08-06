# Examples

## Field types

Every field type is exported from `pydantic_forms.validators` and described in full under
[Field types](reference.md#field-types) in the reference. They fall into a few groups.

**Display-only.** Rendered but collect no input, and all are `frozen`:
[`Label`](reference.md#pydantic_forms.validators.Label),
[`Divider`](reference.md#pydantic_forms.validators.Divider),
[`Hidden`](reference.md#pydantic_forms.validators.Hidden),
[`callout()`](reference.md#pydantic_forms.validators.callout),
[`markdown()`](reference.md#pydantic_forms.validators.markdown),
[`migration_summary()`](reference.md#pydantic_forms.validators.migration_summary),
[`DisplaySubscription`](reference.md#pydantic_forms.validators.DisplaySubscription).

**Text, numbers and dates.** Plain `str`, `int`, `float` and `bool` need no special type and render as text,
number and checkbox inputs. Beyond those:
[`LongText`](reference.md#pydantic_forms.validators.LongText),
[`timestamp()`](reference.md#pydantic_forms.validators.timestamp) /
[`Timestamp`](reference.md#pydantic_forms.validators.Timestamp),
[`Accept`](reference.md#pydantic_forms.validators.Accept),
[`OrganisationId`](reference.md#pydantic_forms.validators.OrganisationId).

**Choices.** [`Choice`](reference.md#pydantic_forms.validators.Choice) for one option,
[`choice_list()`](reference.md#pydantic_forms.validators.choice_list) for several.

**Lists.** [`ListOfOne`](reference.md#pydantic_forms.validators.ListOfOne),
[`ListOfTwo`](reference.md#pydantic_forms.validators.ListOfTwo),
[`unique_conlist()`](reference.md#pydantic_forms.validators.unique_conlist).

**Read-only.** [`read_only_field()`](reference.md#pydantic_forms.validators.read_only_field) for a scalar,
[`read_only_list()`](reference.md#pydantic_forms.validators.read_only_list) for a list.

**Contact persons.** [`ContactPerson`](reference.md#pydantic_forms.validators.ContactPerson) and
[`contact_person_list()`](reference.md#pydantic_forms.validators.contact_person_list).

## A form using them

Field types are ordinary annotations, so a page mixes them freely with plain Python types:

```python
from pydantic_forms.core import FormPage
from pydantic_forms.validators import (
    Choice,
    Divider,
    Label,
    LongText,
    Timestamp,
    choice_list,
)


class Speed(Choice):
    _1000 = ("1000", "1 Gbit/s")
    _10000 = ("10000", "10 Gbit/s")


class Tag(Choice):
    core = ("core", "Core")
    edge = ("edge", "Edge")


class CreatePortForm(FormPage):
    intro: Label = "Configure the new port"
    separator: Divider = None
    description: LongText
    speed: Speed
    tags: choice_list(Tag, min_items=1)
    starts_at: Timestamp
```

Submitting it gives back the validated model, with each value coerced to its annotated type:

```pycon
>>> port = CreatePortForm(
...     description="uplink to core",
...     speed="1000",
...     tags=["core"],
...     starts_at=1735689600,
... )
>>> port.speed
<Speed._1000: '1000'>
>>> port.tags
[<Tag.core: 'core'>]
```

A `Choice` member is a `(value, label)` pair, and the generated schema carries the mapping, so the frontend
can show something friendlier than the stored value:

```pycon
>>> CreatePortForm.model_json_schema()["$defs"]["Speed"]["options"]
{'1000': '1 Gbit/s', '10000': '10 Gbit/s'}
```

The display-only and text types mostly show up as a `format` that the frontend switches on, rather than as
extra validation:

```pycon
>>> CreatePortForm.model_json_schema()["properties"]["description"]["format"]
'long'
>>> CreatePortForm.model_json_schema()["properties"]["intro"]["format"]
'label'
```

## A modify form

A modify form usually lets the user change part of what already exists while showing the rest as context.
`read_only_field` fixes a value and marks it disabled, so the frontend displays it but does not offer it for
editing:

```python
from pydantic_forms.validators import read_only_field


class ModifyPortForm(FormPage):
    port_name: read_only_field("uplink-1")
    speed: read_only_field("1000")
    description: LongText
```

```pycon
>>> ModifyPortForm.model_json_schema()["properties"]["port_name"]["extraProperties"]
{'disabled': True, 'value': 'uplink-1'}
```

The fixed values are normally read from whatever is being modified rather than written as literals, so a form
like this is defined inside the generator, where that data is in hand.

Read-only fields still come back in the result, so the rest of the workflow sees the complete picture:

```pycon
>>> ModifyPortForm(description="uplink to core, upgraded").model_dump()
{'port_name': 'uplink-1', 'speed': '1000', 'description': 'uplink to core, upgraded'}
```

And because each value is fixed, submitting a different one is a validation error rather than a silent
overwrite:

```pycon
>>> ModifyPortForm(port_name="renamed", description="uplink to core")
Traceback (most recent call last):
  ...
pydantic_core._pydantic_core.ValidationError: ...
```

## More examples

For complete form generators in the context of real workflows, see the
[example-orchestrator](https://github.com/workfloworchestrator/example-orchestrator) repository. Its
`workflows/` directory contains multi-page wizards that branch on earlier input, such as
`workflows/l2vpn/create_l2vpn.py`.
