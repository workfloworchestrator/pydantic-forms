from http import HTTPStatus
from typing import ClassVar
from unittest import mock

import pytest
from fastapi.requests import Request

from pydantic_forms.core import FormPage, post_form
from pydantic_forms.exception_handlers.fastapi import form_error_handler
from pydantic_forms.exceptions import FormNotCompleteError
from pydantic_forms.types import FormMeta
from pydantic_forms.utils.json import json_loads


async def test_meta_passed_through_to_response():
    meta: FormMeta = {
        "hasNext": False,
        "customButtons": {"next": {"text": "Confirm", "color": "danger"}},
        "more_data": "test",
    }

    class MetaForm(FormPage):
        meta__: ClassVar[FormMeta] = meta

        name: str

    def form(state):
        yield MetaForm
        return {}

    with pytest.raises(FormNotCompleteError) as error_info:
        post_form(form, {}, [])

    response = await form_error_handler(mock.Mock(spec=Request), error_info.value)

    assert response.status_code == HTTPStatus.NOT_EXTENDED
    body = json_loads(response.body)
    assert body["meta"] == meta
    assert "meta__" not in body["form"]["properties"]
