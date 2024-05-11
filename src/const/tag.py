from __future__ import annotations

import enum


class OpenAPITag(enum.StrEnum):
    def _generate_next_value_(  # type: ignore[override]
        name: str, start: int, count: int, last_values: list[str]
    ) -> str:
        return " ".join(map(lambda x: x.capitalize(), name.split("_")))

    HEALTH_CHECK = enum.auto()
    AUTHN = enum.auto()
    AUTHN_SIGNIN_HISTORY = enum.auto()
    USER = enum.auto()
    USER_FILE = enum.auto()
    WEBHOOK = enum.auto()

    AUTHCO = "AuthCo"
