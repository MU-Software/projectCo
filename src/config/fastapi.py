from __future__ import annotations

import contextlib
import functools
import pathlib
import re
import secrets
import typing

import fastapi.openapi.models
import packaging.version
import pydantic
import pydantic_settings
import toml

import src.config.monitor
import src.config.redis
import src.config.sqlalchemy

AUTHOR_REGEX = re.compile(r"^(?P<name>[\w\s\d\-]+)\s<(?P<email>.+@.+)>$")


class OpenAPISetting(pydantic_settings.BaseSettings):
    # OpenAPI related configs
    # Only available when debug mode is enabled
    docs_url: str | None = "/docs"
    redoc_url: str | None = "/redoc"
    openapi_url: str | None = "/openapi.json"
    openapi_prefix: str | None = ""

    @classmethod
    def blank(cls) -> OpenAPISetting:
        return cls(docs_url=None, redoc_url=None, openapi_url=None, openapi_prefix=None)


class ProjectInfoSetting(pydantic_settings.BaseSettings):
    title: str
    description: str
    version: str
    summary: str | None = None
    terms_of_service: pydantic.HttpUrl | None = None
    contact: fastapi.openapi.models.Contact | None = None
    license: fastapi.openapi.models.License | None = None

    @pydantic.field_validator("version", mode="before")
    @classmethod
    def validate_version(cls, v: str) -> str:
        with contextlib.suppress(packaging.version.InvalidVersion):
            packaging.version.Version(v)
            return v
        raise ValueError(f"Invalid version: {v}")

    @classmethod
    def from_pyproject(cls) -> ProjectInfoSetting:
        project_info: dict = toml.load(pathlib.Path.cwd() / "pyproject.toml")["tool"]["poetry"]

        contact: fastapi.openapi.models.Contact | None = None
        if (authors := project_info.get("authors", None)) and (homepage := project_info.get("homepage", None)):
            if author_info := AUTHOR_REGEX.match(authors[0]):
                contact = fastapi.openapi.models.Contact(
                    name=author_info.group("name"),
                    email=author_info.group("email"),
                    url=homepage,
                )

        return ProjectInfoSetting(
            title=project_info["name"],
            description=project_info["description"],
            version=project_info["version"],
            contact=contact,
        )


class SecuritySetting(pydantic_settings.BaseSettings):
    https_enabled: bool = True
    jwt_algorithm: typing.Literal["HS256"] = "HS256"


class FastAPISetting(pydantic_settings.BaseSettings):
    host: str
    port: int
    root_path: str = ""

    server_name: str = "localhost"
    restapi_version: str = "v1"
    secret_key: pydantic.SecretStr = pydantic.SecretStr(secrets.token_hex(16))
    cors_origin: list[pydantic.AnyHttpUrl] = []

    debug: bool = False

    sqlalchemy: src.config.sqlalchemy.SQLAlchemySetting
    redis: src.config.redis.RedisSetting
    project_info: ProjectInfoSetting = ProjectInfoSetting.from_pyproject()
    openapi: OpenAPISetting = OpenAPISetting()
    security: SecuritySetting = SecuritySetting()
    sentry: src.config.monitor.SentrySetting | None = None

    model_config = pydantic_settings.SettingsConfigDict(extra="ignore")

    @pydantic.model_validator(mode="after")
    def validate_model(self) -> typing.Self:
        if not self.debug:
            self.openapi = OpenAPISetting.blank()

        return self

    def to_fastapi_config(self) -> dict:
        # See fastapi.FastAPI.__init__ keyword arguments for more details
        project_config: dict = self.project_info.model_dump()
        openapi_config: dict = self.openapi.model_dump()
        server_config: dict = {
            "root_path": self.root_path,
            "debug": self.debug,
        }
        return project_config | openapi_config | server_config

    def to_uvicorn_config(self) -> dict:
        # See uvicorn.config.Config.__init__ keyword arguments for more details
        return {
            "host": self.host,
            "port": self.port,
            "reload": self.debug,
        }

    def to_cookie_config(self) -> dict:
        # See src.util.fastapi.cookie.Cookie class for more details
        return {
            "domain": self.server_name if self.debug else None,
            "secure": self.security.https_enabled,
            "httponly": True,
            "samesite": ("none" if self.security.https_enabled else "lax") if self.debug else "strict",
        }


@functools.lru_cache(maxsize=1)
def get_fastapi_setting() -> FastAPISetting:
    return FastAPISetting(
        _env_file=".env",
        _env_file_encoding="utf-8",
        _env_nested_delimiter="__",
        _case_sensitive=False,
    )
