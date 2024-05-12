import itertools
import os
import subprocess  # nosec B404
import typing

import src.config.fastapi

config_obj = src.config.fastapi.get_fastapi_setting()


def db_shell() -> None:
    environ: dict[str, str] = {
        "TZ": "Asia/Seoul",
        "PGPASSWORD": config_obj.sqlalchemy.connection.password,
    }
    kwargs: dict[str, str] = {
        "-U": config_obj.sqlalchemy.connection.username,
        "-h": config_obj.sqlalchemy.connection.host,
        "-p": str(config_obj.sqlalchemy.connection.port),
        "-d": config_obj.sqlalchemy.connection.name,
    }

    psql_cli: list[str] = ["psql"]
    psql_args: list[str] = list(itertools.chain.from_iterable([k, v] for k, v in kwargs.items() if v))
    psql_exec: list[str] = psql_cli + psql_args

    subprocess.run(args=psql_exec, env={**os.environ.copy(), **environ})  # nosec B603


cli_patterns: list[typing.Callable] = [db_shell]
