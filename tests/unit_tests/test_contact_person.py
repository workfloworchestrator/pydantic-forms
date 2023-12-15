from pydantic_core._pydantic_core import ValidationError
from pytest import raises

from pydantic_forms.core import FormPage
from pydantic_forms.validators import ContactPerson


class Form(FormPage):
    contact_person: ContactPerson


def test_contact_person_valid():
    validated_data = Form(contact_person={"name": "test1", "email": "a@b.nl"}).model_dump()

    expected = {"contact_person": {"email": "a@b.nl", "name": "test1", "phone": ""}}

    assert validated_data == expected


def test_contact_person_invalid_email():
    with raises(ValidationError) as error_info:
        invalid_email = "a@b"
        Form(contact_person={"name": "test1", "email": invalid_email, "phone": ""})

    errors = error_info.value.errors(include_url=False, include_context=False)
    expected = [
        {
            "input": "a@b",
            "loc": ("contact_person", "email"),
            "msg": "value is not a valid email address: The part after the @-sign is not "
            "valid. It should have a period.",
            "type": "value_error",
        }
    ]

    assert errors == expected
