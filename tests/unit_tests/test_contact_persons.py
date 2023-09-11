from uuid import uuid4

import pytest
from pydantic import ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.validators import ContactPersonList, contact_person_list


def test_contact_persons():
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

    class OrgContactPersonList(ContactPersonList):
        organisation = org_id
        organisation_key = "key"
        min_items = 1

    class Form(FormPage):
        contact_persons: ContactPersonList = []
        contact_persons_org: OrgContactPersonList
        contact_persons_org2: contact_person_list(org_id, "foo")  # noqa: F821

    expected = {
        "additionalProperties": False,
        "definitions": {
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
                "default": [],
                "items": {"$ref": "#/definitions/ContactPerson"},
                "organisationKey": "organisation",
                "title": "Contact Persons",
                "type": "array",
            },
            "contact_persons_org": {
                "items": {"$ref": "#/definitions/ContactPerson"},
                "organisationId": str(org_id),
                "organisationKey": "key",
                "title": "Contact Persons Org",
                "type": "array",
                "minItems": 1,
            },
            "contact_persons_org2": {
                "items": {"$ref": "#/definitions/ContactPerson"},
                "organisationId": str(org_id),
                "organisationKey": "foo",
                "title": "Contact Persons Org2",
                "type": "array",
            },
        },
        "required": ["contact_persons_org", "contact_persons_org2"],
        "title": "unknown",
        "type": "object",
    }

    assert Form.model_json_schema() == expected


def test_contact_persons_nok():
    org_id = uuid4()

    class ReqContactPersonList(ContactPersonList):
        min_items = 1

    class OrgContactPersonList(ContactPersonList):
        organisation = org_id
        organisation_key = "key"

    class Form(FormPage):
        contact_persons: ReqContactPersonList
        contact_persons_org: OrgContactPersonList = []

    with pytest.raises(ValidationError) as error_info:
        Form(contact_persons=[{"name": "test1", "email": "a@b"}, {"email": "a@b.nl"}])

    expected = [
        {
            "loc": ("contact_persons", 0, "email"),
            "msg": "value is not a valid email address",
            "type": "value_error.email",
        },
        {"loc": ("contact_persons", 1, "name"), "msg": "field required", "type": "value_error.missing"},
    ]
    assert expected == error_info.value.errors()

    with pytest.raises(ValidationError) as error_info:
        Form(contact_persons=[])

    expected = [
        {
            "loc": ("contact_persons",),
            "msg": "ensure this value has at least 1 items",
            "type": "value_error.list.min_items",
            "ctx": {"limit_value": 1},
        }
    ]
    assert expected == error_info.value.errors()
