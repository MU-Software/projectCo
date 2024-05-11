import dataclasses
import datetime
import enum

import src.const.cookie
import src.util.time_util


class UserJWTTokenType(enum.Enum):
    @dataclasses.dataclass(frozen=True)
    class UserJWTTokenTypeSetting:
        refresh_delta: datetime.timedelta
        expiration_delta: datetime.timedelta

    refresh = UserJWTTokenTypeSetting(
        refresh_delta=datetime.timedelta(days=6),
        expiration_delta=datetime.timedelta(days=7),
    )
    access = UserJWTTokenTypeSetting(
        refresh_delta=datetime.timedelta(minutes=15),
        expiration_delta=datetime.timedelta(minutes=30),
    )

    def get_exp_from_now(self) -> datetime.datetime:
        return src.util.time_util.get_utcnow() + self.value.expiration_delta
