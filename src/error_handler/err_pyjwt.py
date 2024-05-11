from __future__ import annotations

import jwt.exceptions

import src.const.error
import src.error_handler.__type__ as err_type


def jwt_error_handler(req: err_type.ReqType, err: jwt.exceptions.PyJWTError) -> err_type.RespType:
    return src.const.error.AuthNError.INVALID_ACCESS_TOKEN().response()


error_handler_patterns = {jwt.exceptions.PyJWTError: jwt_error_handler}
