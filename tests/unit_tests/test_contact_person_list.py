from uuid import uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.validators import contact_person_list


def test_contact_persons():
    ContactPersonList = contact_person_list()

    class Form(FormPage):
        contact_persons: ContactPersonList

    validated_data = Form(
        contact_persons=[{"name": "test1", "email": "a@b.nl", "phone": ""}, {"name": "test2", "email": "a@b.nl"}]
    ).model_dump()

    expected = {
        "contact_persons": [
            {"email": "a@b.nl", "name": "test1", "phone": ""},
            {"email": "a@b.nl", "name": "test2", "phone": ""},
        ]
    }
    assert validated_data == expected


def test_contact_persons_schema():
    org_id = uuid4()

    OrgContactPersonList = contact_person_list(organisation=org_id, organisation_key="key", min_items=1)

    class Form(FormPage):
        contact_persons: contact_person_list()
        contact_persons_org: OrgContactPersonList
        contact_persons_org2: contact_person_list(org_id, "foo")  # noqa: F821

    expected = {
        "additionalProperties": False,
        "$defs": {
            "ContactPerson": {
                "properties": {
                    "email": {"format": "email", "title": "Email", "type": "string"},
                    "name": {"format": "contactPersonName", "title": "Name", "type": "string"},
                    "phone": {"default": "", "title": "Phone", "type": "string"},
                },
                "required": ["name", "email"],
                "title": "ContactPerson",
                "type": "object",
            }
        },
        "properties": {
            "contact_persons": {
                "items": {"$ref": "#/$defs/ContactPerson"},
                "organisationKey": "organisation",
                "title": "Contact Persons",
                "type": "array",
            },
            "contact_persons_org": {
                "items": {"$ref": "#/$defs/ContactPerson"},
                "organisationId": str(org_id),
                "organisationKey": "key",
                "title": "Contact Persons Org",
                "type": "array",
                "minItems": 1,
            },
            "contact_persons_org2": {
                "items": {"$ref": "#/$defs/ContactPerson"},
                "organisationId": str(org_id),
                "organisationKey": "foo",
                "title": "Contact Persons Org2",
                "type": "array",
            },
        },
        "required": ["contact_persons", "contact_persons_org", "contact_persons_org2"],
        "title": "unknown",
        "type": "object",
    }

    assert Form.model_json_schema() == expected


@pytest.fixture(name="Form")
def form_with_contact_person_list():
    org_id = uuid4()

    ReqContactPersonList = contact_person_list(min_items=1)
    OrgContactPersonList = contact_person_list(organisation=org_id, organisation_key="key")

    class Form(FormPage):
        contact_persons: ReqContactPersonList
        contact_persons_org: OrgContactPersonList = []

    return Form


def test_contact_persons_nok_invalid_email(Form):
    with pytest.raises(ValidationError) as error_info:
        Form(contact_persons=[{"name": "test1", "email": "a@b"}, {"email": "a@b.nl"}])

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "input": "a@b",
            "loc": ("contact_persons", 0, "email"),
            "msg": "value is not a valid email address: The part after the @-sign is not valid. It should have a period.",
            "type": "value_error",
        },
        {
            "input": {"email": "a@b.nl"},
            "loc": ("contact_persons", 1, "name"),
            "msg": "Field required",
            "type": "missing",
        },
    ]
    assert errors == expected


def test_contact_persons_nok_empty(Form):
    with pytest.raises(ValidationError) as error_info:
        Form(contact_persons=[])

    errors = error_info.value.errors(include_url=False)
    expected = [
        {
            "input": [],
            "loc": ("contact_persons",),
            "msg": "List should have at least 1 item after validation, not 0",
            "type": "too_short",
            "ctx": {"actual_length": 0, "field_type": "List", "min_length": 1},
        }
    ]
    assert errors == expected


@pytest.mark.parametrize("value", [[], [{}]])
def test_contact_person_list_empty_values(value):
    assert TypeAdapter(contact_person_list()).validate_python(value) == []
