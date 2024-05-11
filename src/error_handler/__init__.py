from __future__ import annotations

import asyncio
import logging
import pathlib

import fastapi

import src.error_handler.__type__ as err_type
import src.util.exception_util
import src.util.import_util

logger = logging.getLogger(__name__)


def get_error_handlers() -> err_type.ErrHandlersDef:
    error_handler_collection: list[err_type.ErrHandlersDef] = src.util.import_util.auto_import_patterns(
        "error_handler_patterns",
        "err_",
        dir=pathlib.Path(__file__).parent,
    )

    def error_logger_decorator(err_handler: err_type.ErrHandlerType) -> err_type.ErrHandlerType:
        async def wrapper(req: fastapi.Request, err: Exception) -> err_type.RespType:
            logger.warning(src.util.exception_util.get_traceback_msg(err))
            return (await response) if asyncio.iscoroutine(response := err_handler(req, err)) else response

        return wrapper

    return {k: error_logger_decorator(v) for d in error_handler_collection for k, v in d.items()}
