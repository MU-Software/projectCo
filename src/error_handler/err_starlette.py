from __future__ import annotations

import fastapi.exception_handlers
import starlette.exceptions

import src.const.error
import src.error_handler.__type__ as err_type
import src.util.string_util


async def fastapi_http_exception_handler(
    req: err_type.ReqType,
    err: fastapi.exceptions.HTTPException,
) -> err_type.RespType:
    return await fastapi.exception_handlers.http_exception_handler(req, err)


def starlette_http_exception_handler(
    req: err_type.ReqType,
    err: starlette.exceptions.HTTPException,
) -> err_type.RespType:
    response = src.const.error.ErrorStruct(
        status_code=err.status_code,
        type=src.util.string_util.camel_to_snake_case(err.__class__.__name__),
        msg=err.detail,
        headers=err.headers,
    ).response()
    response.headers.update(err.headers or {})
    return response


error_handler_patterns = {
    fastapi.exceptions.HTTPException: fastapi_http_exception_handler,
    starlette.exceptions.HTTPException: starlette_http_exception_handler,
}
