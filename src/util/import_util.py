import pathlib
import typing

import src.util.stdlib_util

T = typing.TypeVar("T")


def auto_import_objs(pattern_name: str, file_prefix: str, dir: pathlib.Path) -> list[T]:
    collected_objs: list[T] = []
    for module_path in dir.glob(f"**/{file_prefix}*.py"):
        if module_path.stem.startswith("__"):
            continue

        if obj := typing.cast(T, getattr(src.util.stdlib_util.load_module(module_path), pattern_name, None)):
            collected_objs.append(obj)
    return collected_objs


def auto_import_patterns(pattern_name: str, file_prefix: str, dir: pathlib.Path) -> list[T]:
    return list(filter(src.util.stdlib_util.isiterable, auto_import_objs(pattern_name, file_prefix, dir)))
