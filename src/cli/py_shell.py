import contextlib
import datetime
import pathlib
import typing

import IPython
import IPython.terminal.ipapp
import pydantic
import sqlalchemy

import src.config.fastapi
import src.db
import src.db.model
import src.redis

DEFAULT_IMPORT_NAMESPACE = {
    **src.db.model.__dict__,
    "datetime": datetime,
    "pt": pathlib,
    "pathlib": pathlib,
    "typing": typing,
    "pydantic": pydantic,
    "sa": sqlalchemy,
    "sqlalchemy": sqlalchemy,
}


def py_shell() -> None:
    """IPython shell을 실행합니다."""
    config_obj = src.config.fastapi.get_fastapi_setting()
    sync_db = src.db.SyncDB(config_obj=config_obj)
    sync_redis = src.redis.SyncRedis(config_obj=config_obj)

    with contextlib.ExitStack() as init_stack:
        init_stack.enter_context(sync_db)  # type: ignore[arg-type]
        init_stack.enter_context(sync_redis)  # type: ignore[arg-type]

        with contextlib.ExitStack() as ipy_stack:
            ipy_namespace = DEFAULT_IMPORT_NAMESPACE | {
                "config": config_obj,
                "db_session": ipy_stack.enter_context(sync_db.get_sync_session()),
                "redis_session": ipy_stack.enter_context(sync_redis.get_sync_session()),
            }

            IPython.start_ipython(argv=[], user_ns=ipy_namespace)


cli_patterns: list[typing.Callable] = [py_shell]
