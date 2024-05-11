import datetime
import typing

import fastapi
import pydantic

import src.const.time
import src.util.time_util


class Cookie(pydantic.BaseModel):
    key: str
    value: str = ""
    # Max-Age는 expires로 대체됨
    expires: datetime.datetime | None = pydantic.Field(default=None, validate_default=True)
    path: str = "/"
    domain: str | None = None
    secure: bool = False
    httponly: bool = False
    samesite: typing.Literal["lax", "strict", "none"] = "lax"

    @pydantic.field_validator("expires", mode="before")
    def validate_expires(cls, v: src.util.time_util.DateTimeableType = None) -> datetime.datetime | None:
        return src.util.time_util.try_parse_datetime(v, raise_if_not_parseable=True)

    @pydantic.model_validator(mode="after")
    def validate_samesite(self) -> typing.Self:
        if self.samesite == "none" and not self.secure:
            raise ValueError("samesite가 none인 경우 secure는 반드시 True여야 합니다.")
        return self

    @pydantic.field_serializer("expires", when_used="always")
    def serialize_expires(self, v: datetime.datetime | None) -> str | None:
        return v.strftime(src.const.time.RFC_7231_GMT_DATETIME_FORMAT) if v else None

    def set_cookie(self, response: fastapi.Response) -> None:
        response.set_cookie(**self.model_dump(by_alias=True))

    def delete_cookie(self, response: fastapi.Response) -> None:
        response.delete_cookie(**self.model_dump(by_alias=True, exclude={"value", "expires"}))
