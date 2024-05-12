import pathlib
import typing

import typer

import src.util.stdlib_util

typer_app = typer.Typer()

current_dir = pathlib.Path(__file__).parent
for module_path in current_dir.glob("*.py"):
    if module_path.stem.startswith("__"):
        continue
    module = src.util.stdlib_util.load_module(module_path)

    cli_patterns: list[typing.Callable]
    if not src.util.stdlib_util.isiterable(cli_patterns := getattr(module, "cli_patterns", None)):
        continue

    for cli_func in cli_patterns:
        typer_app.command()(cli_func)
