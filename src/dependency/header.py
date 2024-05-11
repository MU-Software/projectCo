import typing

import fastapi

import src.const.cookie
import src.const.header


def get_user_ip(
    request: fastapi.Request,
    real_ip: typing.Annotated[str | None, src.const.header.HeaderKey.REAL_IP.as_header()] = None,
    forwarded_for: typing.Annotated[str | None, src.const.header.HeaderKey.FORWARDED_FOR.as_header()] = None,
) -> str | None:
    return real_ip or forwarded_for or (request.client.host if request.client else None)


user_ip = typing.Annotated[str | None, fastapi.Depends(get_user_ip)]
user_agent = typing.Annotated[str | None, src.const.header.HeaderKey.USER_AGENT.as_header()]
csrf_token = typing.Annotated[str | None, src.const.cookie.CookieKey.CSRF_TOKEN.as_cookie()]
