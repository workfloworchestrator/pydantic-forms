from pydantic_forms.core import FormPage
from pydantic_forms.validators import OrganisationId


def test_organisation_id_schema():
    class Form(FormPage):
        org_id: OrganisationId

    expected = {
        "additionalProperties": False,
        "properties": {
            "org_id": {
                "format": "organisationId",
                "title": "Org Id",
                "type": "string",
            }
        },
        "required": ["org_id"],
        "title": "unknown",
        "type": "object",
    }

    assert Form.model_json_schema() == expected
