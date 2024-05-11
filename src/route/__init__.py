from __future__ import annotations

import pathlib

import fastapi

import src.util.import_util


def get_routes() -> list[fastapi.APIRouter]:
    return src.util.import_util.auto_import_objs("router", "", pathlib.Path(__file__).parent)
