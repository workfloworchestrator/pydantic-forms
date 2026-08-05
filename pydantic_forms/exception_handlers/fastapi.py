# Copyright 2019-2023 SURF.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

# TODO Decide how to expose this so pydantic-forms can be framework agnostic
from http import HTTPStatus
from typing import Any

import structlog
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from pydantic_forms.exceptions import (
    FormException,
    FormNotCompleteError,
    FormNotFoundError,
    FormValidationError,
    show_ex,
)
from pydantic_forms.utils.json import json_dumps, json_loads

logger = structlog.get_logger(__name__)


async def form_error_handler(request: Request, exc: FormException) -> JSONResponse:
    match exc:
        case FormValidationError():
            status = HTTPStatus.BAD_REQUEST
            base_content = _create_content(exc, status, "Form not valid")
            detail_content = base_content | {
                "validation_errors": json_loads(json_dumps(exc.errors)),
            }
            debug_content = _add_traceback(exc, detail_content)
            return JSONResponse(debug_content, status_code=status)

        case FormNotCompleteError():
            status = HTTPStatus.NOT_EXTENDED
            base_content = _create_content(exc, status, "Form not complete")
            detail_content = base_content | {
                "form": json_loads(json_dumps(exc.form)),
                "meta": getattr(exc, "meta", None),
            }
            debug_content = _add_traceback(exc, detail_content)
            return JSONResponse(debug_content, status_code=status)

        case FormNotFoundError():
            status = HTTPStatus.NOT_FOUND
            base_content = _create_content(exc, status, "Form not found")
            return JSONResponse(base_content, status_code=status)

        case _:
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            base_content = _create_content(exc, status, "Internal Server Error")
            return JSONResponse(base_content, status_code=status)


def _create_content(exc: FormException, status: HTTPStatus, title: str) -> dict[str, str | HTTPStatus]:
    return {
        "type": type(exc).__name__,
        "detail": str(exc),
        "title": title,
        "status": status,
    }


def _add_traceback(exc: FormException, content: dict[str, Any]) -> dict[str, Any]:
    LOG_LEVEL_PYDANTIC_FORMS = "DEBUG" if os.getenv("LOG_LEVEL_PYDANTIC_FORMS", "INFO").upper() == "DEBUG" else "INFO"
    if LOG_LEVEL_PYDANTIC_FORMS == "DEBUG":
        content_with_traceback = content | {"traceback": show_ex(exc)}
        logger.debug("Form validation Response", result=content_with_traceback)
        return content_with_traceback

    return content
