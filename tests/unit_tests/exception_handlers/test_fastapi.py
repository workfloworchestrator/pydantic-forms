from http import HTTPStatus
from unittest import mock

import pytest
from fastapi.requests import Request
from pydantic import ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.exception_handlers.fastapi import form_error_handler
from pydantic_forms.exceptions import FormNotCompleteError, FormOverflowError, FormValidationError


async def test_form_not_complete():
    exception = FormNotCompleteError({"message": "foobar"})
    response = await form_error_handler(mock.Mock(spec=Request), exception)
    assert response.status_code == HTTPStatus.NOT_EXTENDED
    body = response.body.decode()
    assert "FormNotCompleteError" in body
    assert "foobar" in body


@pytest.fixture
def example_form_error_invalid_int():
    class Form(FormPage):
        number: int

    with pytest.raises(ValidationError) as error_info:
        assert Form(number="foo")

    return error_info.value


async def test_form_validation(example_form_error_invalid_int):
    exception = FormValidationError("myvalidator", example_form_error_invalid_int)
    response = await form_error_handler(mock.Mock(spec=Request), exception)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    body = response.body.decode()
    assert "FormValidationError" in body
    assert "should be a valid integer" in body


async def test_overflow_error():
    exception = FormOverflowError("my error")
    response = await form_error_handler(mock.Mock(spec=Request), exception)
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    body = response.body.decode()
    assert "FormOverflowError" in body
    assert "my error" in body
