from __future__ import annotations

import contextlib
import logging
import typing

import billiard.einfo
import celery
import celery.app.task
import celery.result

import src.config.celery
import src.db
import src.redis
import src.util.exception_util
import src.util.string_util

logger = logging.getLogger(__name__)

T = typing.TypeVar("T")
EInfoType = typing.TypeVar("EInfoType", bound=billiard.einfo.ExceptionInfo)


class SessionTask(celery.Task, typing.Generic[T]):
    config_obj: src.config.celery.CelerySetting
    sync_db: src.db.SyncDB
    sync_redis: src.redis.SyncRedis

    track_started = True
    default_retry_delay = 60  # Retry after 1 minute.

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.config_obj = src.config.celery.get_celery_setting()
        self.sync_db = src.db.SyncDB(config_obj=self.config_obj)
        with self.sync_db:
            # With opening DB connection, we can check if DB is connected.
            pass

        self.sync_redis = src.redis.SyncRedis(config_obj=self.config_obj)
        with self.sync_redis:
            # Like DB, we can check if Redis is connected with opening the connection.
            pass

    def __del__(self) -> None:
        self.close_connections()

    def open_connections(self) -> None:
        self.sync_db.open()
        self.sync_redis.open()

    def close_connections(self) -> None:
        with contextlib.suppress(Exception):
            self.sync_db.close()
        with contextlib.suppress(Exception):
            self.sync_redis.close()

    @property
    def db_opened(self) -> bool:
        return all([self.sync_db.engine, self.sync_db.session_maker])

    @property
    def task_id(self) -> str | None:
        return typing.cast(str | None, typing.cast(celery.app.task.Context, self.request).id)

    def check_db_queryable(self) -> None:
        if not self.db_opened:
            raise RuntimeError("DB is not opened")

        if not self.task_id:
            raise RuntimeError("Task ID is not set")

    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        """
        This method is called when the task is about to be executed.
        Notes that this method will be called every time the task is executed, even if the task is retried.
        """
        logger.warning(f"Task[{task_id}] before_start called")
        self.open_connections()
        return super().before_start(self.task_id, args, kwargs)

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: EInfoType) -> None:
        """
        This method is called when the task will be retried.
        Notes that this method will be called before the retry delay is applied.
        """
        logger.warning(f"Task[{task_id}] on_retry called")
        return super().on_retry(exc, self.task_id, args, kwargs, einfo)

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: EInfoType) -> None:
        """
        This method is called when the task raised an exception,
        and failed so that it will not be retried.
        """
        logger.warning(f"Task[{task_id}] on_failure called:\n{src.util.exception_util.get_traceback_msg(einfo)}")
        return super().on_failure(exc, self.task_id, args, kwargs, einfo)

    def on_success(self, retval: T, task_id: str, args: tuple, kwargs: dict) -> None:
        """
        This method is called when the task has been successfully executed.
        """
        logger.warning(f"Task[{task_id}] on_success called")
        return super().on_success(retval, self.task_id, args, kwargs)

    def after_return(self, status: str, retval: T, task_id: str, args: tuple, kwargs: dict, einfo: EInfoType) -> None:
        """
        This method is called after the task has returned, after on_success or on_failure has been called.
        """
        logger.warning(f"Task[{task_id}] after_return called: {status} (retval: {retval}, einfo: {einfo})")
        self.close_connections()
        return super().after_return(status, retval, self.task_id, args, kwargs, einfo)
