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


# TODO Decide how to expose this so pydantic-forms can be framework agnostic

from http import HTTPStatus

from fastapi.requests import Request
from fastapi.responses import JSONResponse

from pydantic_forms.exceptions import FormException, FormNotCompleteError, FormValidationError, show_ex
from pydantic_forms.utils.json import json_dumps, json_loads


async def form_error_handler(request: Request, exc: FormException) -> JSONResponse:
    if isinstance(exc, FormValidationError):
        return JSONResponse(
            {
                "type": type(exc).__name__,
                "detail": str(exc),
                "traceback": show_ex(exc),
                "title": "Form not valid",
                # We need to make sure the is nothing the default json.dumps cannot handle
                "validation_errors": json_loads(json_dumps(exc.errors)),
                "status": HTTPStatus.BAD_REQUEST,
            },
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if isinstance(exc, FormNotCompleteError):
        return JSONResponse(
            {
                "type": type(exc).__name__,
                "detail": str(exc),
                "traceback": show_ex(exc),
                # We need to make sure the is nothing the default json.dumps cannot handle
                "form": json_loads(json_dumps(exc.form)),
                "title": "Form not complete",
                "status": HTTPStatus.NOT_EXTENDED,
            },
            status_code=HTTPStatus.NOT_EXTENDED,
        )

    return JSONResponse(
        {
            "detail": str(exc),
            "title": "Internal Server Error",
            "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            "type": type(exc).__name__,
        },
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
    )
