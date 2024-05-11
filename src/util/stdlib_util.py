import contextlib
import importlib.util
import json
import pathlib
import types
import typing

import src.util.exception_util

safe_int: typing.Callable[[typing.Any], int] = src.util.exception_util.ignore_exception(Exception, 0)(int)
safe_json_loads: typing.Callable[[typing.Any], dict | None] = src.util.exception_util.ignore_exception(Exception, None)(
    json.loads
)


def isiterable(a: typing.Any) -> bool:
    with contextlib.suppress(TypeError):
        return iter(a) is not None
    return False


def load_module(module_path: pathlib.Path) -> types.ModuleType:
    if not module_path.is_file():
        raise ValueError(f"module_path must be file path: {module_path}")

    module_path = module_path.resolve()
    module_name = module_path.stem
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module
