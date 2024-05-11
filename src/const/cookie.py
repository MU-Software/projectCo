import dataclasses
import datetime
import enum

import fastapi
import fastapi.params

import src.const.time


class CookieKey(enum.Enum):
    @dataclasses.dataclass(frozen=True)
    class CookieKeyData:
        path: str
        expires: datetime.datetime | None = None
        alias: str | None = None

    CSRF_TOKEN = CookieKeyData(path="/", expires=src.const.time.NEVER_EXPIRE_COOKIE_DATETIME)
    REFRESH_TOKEN = CookieKeyData(path="/authn/")

    def get_name(self) -> str:
        return (self.name if self.value.alias is None else self.value.alias).lower()

    def as_cookie(self) -> fastapi.params.Cookie:
        return fastapi.Cookie(alias=self.get_name(), include_in_schema=False)

    def to_cookie_config(self) -> dict[str, str]:
        result: dict[str, str | None] = {
            "key": self.get_name(),
            "path": self.value.path,
            "expires": self.value.expires,
        }
        return {k: v for k, v in result.items() if v is not None}
