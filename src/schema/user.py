from __future__ import annotations

import datetime
import typing
import uuid

import argon2
import jwt
import pydantic
import pydantic_core

import src.config.fastapi
import src.const.jwt
import src.db.model.user as user_model
import src.util.json_util
import src.util.pydantic.normalizer as normalizer
import src.util.pydantic.with_model as with_model
import src.util.string_util
import src.util.time_util


class UserDTO(pydantic.BaseModel):
    uuid: uuid.UUID
    username: src.util.string_util.UsernameField
    nickname: str
    email: pydantic.EmailStr
    email_verified_at: pydantic.PastDatetime | None = None

    created_at: datetime.datetime
    modified_at: datetime.datetime
    deleted_at: datetime.datetime | None = None
    locked_at: datetime.datetime | None = None
    last_signin_at: datetime.datetime | None = None

    private: bool = False
    description: str | None = None
    profile_image: str | None = None
    website: str | None = None
    location: str | None = None

    model_config = pydantic.ConfigDict(from_attributes=True)


class UserCreate(normalizer.NormalizerModelMixin):  # A.k.a. Sign Up
    username: src.util.string_util.UsernameField
    nickname: str
    email: pydantic.EmailStr

    password: src.util.string_util.PasswordField
    password_confirm: str = pydantic.Field(exclude=True)

    private: bool = False
    description: str | None = None
    profile_image: str | None = None
    website: str | None = None
    location: str | None = None
    birth: datetime.date | None = None

    @pydantic.model_validator(mode="after")
    def validate_model(self) -> typing.Self:
        if self.password != self.password_confirm:
            raise ValueError("확인을 위해 다시 입력해주신 비밀번호가 일치하지 않아요, 다시 한 번 확인해주세요!")

        password_containable_fields = (self.email, self.username, self.nickname)
        if any(self.password.lower() in z.lower() for z in password_containable_fields):
            raise ValueError("비밀번호가 ID, 이메일, 또는 닉네임과 너무 비슷해요! 다른 비밀번호를 입력해주세요!")

        return self

    @pydantic.field_serializer("password", when_used="always")
    def serialize_password(self, v: str) -> str:
        """DB에 비밀번호의 해시를 저장하도록 합니다."""
        return argon2.PasswordHasher().hash(v)


class UserUpdate(normalizer.NormalizerModelMixin, with_model.WithSAModelMixin[user_model.User]):
    username: src.util.string_util.UsernameField
    nickname: str

    private: bool = False
    description: str | None = None
    profile_image: str | None = None
    website: str | None = None
    location: str | None = None
    birth: datetime.date | None = None


class UserPasswordUpdate(normalizer.NormalizerModelMixin):
    original_password: src.util.string_util.PasswordField = pydantic.Field(exclude=True)
    new_password: src.util.string_util.PasswordField = pydantic.Field(exclude=True)
    new_password_confirm: str = pydantic.Field(exclude=True)

    @pydantic.model_validator(mode="after")
    def validate_model(self) -> typing.Self:
        if self.new_password != self.new_password_confirm:
            raise ValueError("확인을 위해 다시 입력해주신 비밀번호가 일치하지 않아요, 다시 한 번 확인해주세요!")

        return self


class UserPasswordUpdateForModel(UserPasswordUpdate, with_model.WithSAModelMixin[user_model.User]):
    username: src.util.string_util.UsernameField = pydantic.Field(exclude=True)
    nickname: str = pydantic.Field(exclude=True)
    email: pydantic.EmailStr = pydantic.Field(exclude=True)

    locked_at: datetime.datetime | None = pydantic.Field(exclude=True)
    deleted_at: datetime.datetime | None = pydantic.Field(exclude=True)

    password: str  # DB record of current password, hashed

    @pydantic.field_validator("original_password", mode="after")
    @classmethod
    def validate_original_password(cls, value: str, info: pydantic_core.core_schema.ValidationInfo) -> str:
        try:
            argon2.PasswordHasher().verify(info.data["password"], value)
        except argon2.exceptions.VerifyMismatchError:
            raise ValueError("기존 비밀번호와 일치하지 않아요!")

        return value

    @pydantic.model_validator(mode="after")
    def validate_model(self) -> typing.Self:
        super().validate_model()

        password_containable_fields = (self.username, self.nickname, self.email)
        if any(self.password.lower() in z.lower() for z in password_containable_fields):
            raise ValueError("비밀번호가 ID, 이메일, 또는 닉네임과 너무 비슷해요! 다른 비밀번호를 입력해주세요!")

        return self


class UserSignIn(normalizer.NormalizerModelMixin):
    username: src.util.string_util.UsernameField | pydantic.EmailStr | str
    password: str


class UserJWTToken(pydantic.BaseModel):
    # Registered Claim
    iss: str  # Token Issuer(Fixed)
    exp: pydantic.FutureDatetime  # Expiration Unix Time
    sub: src.const.jwt.UserJWTTokenType  # Token name
    jti: uuid.UUID  # JWT token ID

    # Private Claim
    user: uuid.UUID  # Audience, User, Token holder

    # Public Claim
    user_agent: str  # User-Agent from Token
    request_user_agent: str = pydantic.Field(exclude=True)  # User-Agent from Request

    # For encryption and decryption
    key: str = pydantic.Field(exclude=True)
    config_obj: src.config.fastapi.FastAPISetting = pydantic.Field(exclude=True)

    JWT_FIELD: typing.ClassVar[set[str]] = {"iss", "exp", "sub", "jti", "user", "user_agent"}

    @classmethod
    def from_token(
        cls, token: str, key: str, request_user_agent: str, config_obj: src.config.fastapi.FastAPISetting
    ) -> UserJWTToken:
        return cls(
            **jwt.decode(jwt=token, key=key, algorithms=["HS256"]),
            key=key,
            request_user_agent=request_user_agent,
            config_obj=config_obj,
        )

    @property
    def jwt(self) -> str:
        payload = {k: v for k, v in dict(self).items() if k in self.JWT_FIELD}
        payload = src.util.json_util.dict_to_jsonable_dict(payload | {"exp": self.exp.timestamp()})
        return jwt.encode(payload=payload, key=self.key)

    @pydantic.field_validator("sub", mode="before")
    @classmethod
    def validate_sub(cls, sub: str | src.const.jwt.UserJWTTokenType) -> src.const.jwt.UserJWTTokenType:
        return sub if isinstance(sub, src.const.jwt.UserJWTTokenType) else src.const.jwt.UserJWTTokenType[sub]

    @pydantic.model_validator(mode="after")
    def validate_model(self) -> typing.Self:
        if not src.util.string_util.compare_user_agent(self.request_user_agent, self.user_agent):
            raise jwt.exceptions.InvalidTokenError("User-Agent does not compatable")

        return self

    @pydantic.field_serializer("exp", when_used="always")
    def serialize_exp(self, exp: datetime.datetime) -> int:
        return int(exp.timestamp())

    @pydantic.field_serializer("sub", when_used="always")
    def serialize_sub(self, sub: src.const.jwt.UserJWTTokenType) -> str:
        return sub.name

    @property
    def claimed_at(self) -> datetime.datetime:
        return self.exp - self.sub.value.expiration_delta

    @property
    def refreshes_at(self) -> datetime.datetime:
        return self.claimed_at + self.sub.value.refresh_delta

    @property
    def should_refresh(self) -> bool:
        return self.refreshes_at < src.util.time_util.get_utcnow()


class RefreshToken(UserJWTToken):
    sub: typing.Literal[src.const.jwt.UserJWTTokenType.refresh]

    @classmethod
    def from_orm(
        cls, signin_history: user_model.UserSignInHistory, config_obj: src.config.fastapi.FastAPISetting
    ) -> RefreshToken:
        return cls(
            iss=config_obj.server_name,
            exp=signin_history.expires_at,
            sub=src.const.jwt.UserJWTTokenType.refresh,
            jti=signin_history.uuid,
            user=signin_history.user_uuid,
            user_agent=signin_history.user_agent,
            request_user_agent=signin_history.user_agent,
            key=config_obj.secret_key.get_secret_value(),
            config_obj=config_obj,
        )

    @pydantic.model_serializer(mode="plain", when_used="always")
    def serialize_model(self) -> dict[str, str | datetime.datetime]:
        return {"exp": self.exp}

    def to_access_token(self, csrf_token: str) -> AccessToken:
        return AccessToken.model_validate(
            dict(self)
            | {
                "key": self.key + csrf_token,
                "sub": src.const.jwt.UserJWTTokenType.access,
                "exp": src.util.time_util.get_utcnow() + src.const.jwt.UserJWTTokenType.access.value.expiration_delta,
            }
        )


class AccessToken(UserJWTToken):
    sub: typing.Literal[src.const.jwt.UserJWTTokenType.access]

    @pydantic.model_serializer(mode="plain", when_used="always")
    def serialize_model(self) -> dict[str, str | datetime.datetime]:
        return {"token": self.jwt, "exp": self.exp}


class UserTokenResponse(pydantic.BaseModel):
    access_token: str
    token_type: typing.Literal["bearer"] = "bearer"
