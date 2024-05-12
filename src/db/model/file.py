import sqlalchemy.orm as sa_orm

import src.db.__mixin__ as db_mixin
import src.db.__type__ as db_types


class File(db_mixin.DefaultModelMixin):
    mimetype: sa_orm.Mapped[db_types.Str_Nullable]
    path: sa_orm.Mapped[db_types.Str]  # S3 Key
    hash: sa_orm.Mapped[db_types.Str]
    size: sa_orm.Mapped[int]

    data: sa_orm.Mapped[db_types.Json_Nullable]

    created_by_uuid: sa_orm.Mapped[db_types.UserFK]
    deleted_by_uuid: sa_orm.Mapped[db_types.UserFK_Nullable]
    locked_by_uuid: sa_orm.Mapped[db_types.UserFK_Nullable]
    locked_at: sa_orm.Mapped[db_types.DateTime_Nullable]
    locked_reason: sa_orm.Mapped[db_types.Str_Nullable]

    private: sa_orm.Mapped[db_types.Bool_DFalse]
    readable: sa_orm.Mapped[db_types.Bool_DTrue]
    writable: sa_orm.Mapped[db_types.Bool_DFalse]
