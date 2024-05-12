from __future__ import annotations

import datetime
import uuid

import pydantic

import src.config.fastapi
import src.const.jwt
import src.util.time_util


class UserSignInHistoryDTO(pydantic.BaseModel):
    uuid: uuid.UUID

    ip: pydantic.IPvAnyAddress
    user_agent: str

    created_at: datetime.datetime
    modified_at: datetime.datetime
    deleted_at: datetime.datetime | None = None
    expires_at: datetime.datetime

    model_config = pydantic.ConfigDict(from_attributes=True)


class UserSignInHistoryCreate(pydantic.BaseModel):
    user_uuid: uuid.UUID
    ip: pydantic.IPvAnyAddress
    user_agent: str
    config_obj: src.config.fastapi.FastAPISetting = pydantic.Field(exclude=True)
    client_token: str | None = None

    @pydantic.field_serializer("ip", when_used="always")
    def serialize_ip(self, v: pydantic.IPvAnyAddress) -> str:
        # if we save v directly, it will be saved as a ip range in the database
        return str(v)

    @pydantic.computed_field  # type: ignore[misc]
    @property
    def expires_at(self) -> datetime.datetime:
        return src.util.time_util.get_utcnow() + src.const.jwt.UserJWTTokenType.refresh.value.expiration_delta
