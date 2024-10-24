from http import HTTPStatus
from unittest import mock

import pytest
from fastapi.requests import Request
from pydantic import ValidationError
from pydantic_i18n import PydanticI18n

from pydantic_forms.core import FormPage
from pydantic_forms.core.translations import translations
from pydantic_forms.exception_handlers.fastapi import form_error_handler
from pydantic_forms.exceptions import FormNotCompleteError, FormOverflowError, FormValidationError


async def test_form_not_complete():
    exception = FormNotCompleteError({"message": "foobar"})
    response = await form_error_handler(mock.Mock(spec=Request), exception)
    assert response.status_code == HTTPStatus.NOT_EXTENDED
    body = response.body.decode()
    assert "FormNotCompleteError" in body
    assert "foobar" in body
    assert "traceback" not in body


async def test_form_not_complete_with_stack_trace(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL_PYDANTIC_FORMS", "DEBUG")
    exception = FormNotCompleteError({"message": "foobar"})
    response = await form_error_handler(mock.Mock(spec=Request), exception)
    assert response.status_code == HTTPStatus.NOT_EXTENDED
    body = response.body.decode()
    assert "FormNotCompleteError" in body
    assert "foobar" in body
    assert "traceback" in body


@pytest.fixture
def example_form_error_invalid_int():
    class Form(FormPage):
        number: int

    with pytest.raises(ValidationError) as error_info:
        assert Form(number="foo")

    return error_info.value


async def test_form_validation(example_form_error_invalid_int):
    tr = PydanticI18n(translations)
    exception = FormValidationError("myvalidator", example_form_error_invalid_int, tr)
    response = await form_error_handler(mock.Mock(spec=Request), exception)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    body = response.body.decode()
    assert "FormValidationError" in body
    assert "should be a valid integer" in body
    assert "traceback" not in body


async def test_form_validation_nl_NL(example_form_error_invalid_int):
    tr = PydanticI18n(translations)
    exception = FormValidationError("myvalidator", example_form_error_invalid_int, tr, "nl_NL")
    response = await form_error_handler(mock.Mock(spec=Request), exception)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    body = response.body.decode()
    assert "FormValidationError" in body
    assert "Invoer moet een geldig geheel getal zijn" in body
    assert "traceback" not in body


async def test_form_validation_with_stack_trace(example_form_error_invalid_int, monkeypatch):
    monkeypatch.setenv("LOG_LEVEL_PYDANTIC_FORMS", "DEBUG")
    tr = PydanticI18n(translations)
    exception = FormValidationError("myvalidator", example_form_error_invalid_int, tr)
    response = await form_error_handler(mock.Mock(spec=Request), exception)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    body = response.body.decode()
    assert "FormValidationError" in body
    assert "should be a valid integer" in body
    assert "traceback" in body


async def test_overflow_error():
    exception = FormOverflowError("my error")
    response = await form_error_handler(mock.Mock(spec=Request), exception)
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    body = response.body.decode()
    assert "FormOverflowError" in body
    assert "my error" in body
