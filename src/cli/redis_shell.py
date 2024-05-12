import itertools
import os
import subprocess  # nosec B404
import typing

import src.config.fastapi

config_obj = src.config.fastapi.get_fastapi_setting()


def redis_shell() -> None:
    environ: dict[str, str] = {
        "TZ": "Asia/Seoul",
        "REDISCLI_AUTH": config_obj.redis.password or "",
    }
    kwargs: dict[str, str] = {
        "--user": config_obj.redis.username or "",
        "-h": config_obj.redis.host,
        "-p": str(config_obj.redis.port),
        "-n": str(config_obj.redis.db),
    }

    redis_cli: list[str] = ["redis-cli"]
    redis_args: list[str] = list(itertools.chain.from_iterable([k, v] for k, v in kwargs.items() if v))
    redis_exec: list[str] = redis_cli + redis_args

    subprocess.run(args=redis_exec, env={**os.environ.copy(), **environ})  # nosec B603


cli_patterns: list[typing.Callable] = [redis_shell]
