import functools
import typing

import pydantic
import pydantic_settings

import src.config.monitor
import src.config.redis
import src.config.sqlalchemy

LOGLEVEL = typing.Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class CelerySetting(pydantic_settings.BaseSettings):
    debug: bool = False

    redis: src.config.redis.RedisSetting
    broker_url: str | None = None

    sqlalchemy: src.config.sqlalchemy.SQLAlchemySetting
    result_backend: str | None = None
    result_extended: bool = True
    result_expires: int | None = None

    imports: list[str] = ["src.celery_task.task"]

    task_remote_tracebacks: bool = True
    task_track_started: bool = True
    task_send_sent_event: bool = True
    worker_send_task_events: bool = True
    worker_prefetch_multiplier: int = 1
    worker_redirect_stdouts_level: LOGLEVEL = "DEBUG"

    sentry: src.config.monitor.SentrySetting | None = None

    model_config = pydantic_settings.SettingsConfigDict(extra="ignore")

    @pydantic.model_validator(mode="after")
    def assemble_urls(self) -> typing.Self:
        self.broker_url = self.redis.uri

        # We need to replace the scheme of the URL from postgresql to db.
        self.result_backend = "db+" + str(self.sqlalchemy.dsn)
        return self


@functools.lru_cache(maxsize=1)
def get_celery_setting() -> CelerySetting:
    return CelerySetting(
        _env_file=".env",
        _env_file_encoding="utf-8",
        _env_nested_delimiter="__",
        _case_sensitive=False,
    )
