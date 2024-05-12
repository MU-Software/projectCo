import datetime
import typing
import uuid

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_ext_asyncio
import sqlalchemy.orm as sa_orm
import sqlalchemy.sql.roles as sa_role

Ss = typing.TypeVar("Ss", bound=sa_orm.Session)
As = typing.TypeVar("As", bound=sa_ext_asyncio.AsyncSession)
Ps = typing.TypeVar("Ps", sa_orm.Session, sa_ext_asyncio.AsyncSession)
ColumnableType: typing.TypeAlias = str | sa.Column | sa_role.DDLConstraintColumnRole | sa_orm.Mapped
PKRelatedType: typing.TypeAlias = typing.Annotated[type[uuid.UUID], sa_orm.Mapped]


def ForeignKeyTypeGenerator(columninfo: ColumnableType) -> PKRelatedType:
    return typing.Annotated[  # type: ignore[return-value]
        uuid.UUID, sa_orm.mapped_column(sa.ForeignKey(columninfo), nullable=False, index=True)
    ]


def NullableForeignKeyTypeGenerator(columninfo: ColumnableType) -> PKRelatedType:
    return typing.Annotated[  # type: ignore[return-value]
        uuid.UUID, sa_orm.mapped_column(sa.ForeignKey(columninfo), nullable=True, index=True)
    ]


PrimaryKeyType = typing.Annotated[
    uuid.UUID,
    sa_orm.mapped_column(primary_key=True, default=uuid.uuid4, unique=True, index=True, nullable=False),
]

Bool_DTrue = typing.Annotated[bool, sa_orm.mapped_column(default=True, nullable=False)]
Bool_DFalse = typing.Annotated[bool, sa_orm.mapped_column(default=False, nullable=False)]

Str = typing.Annotated[str, sa_orm.mapped_column(nullable=False)]
Str_Unique = typing.Annotated[str, sa_orm.mapped_column(nullable=False, unique=True, index=True)]
Str_Nullable = typing.Annotated[str | None, sa_orm.mapped_column(nullable=True)]

DateTime = typing.Annotated[datetime.datetime, sa_orm.mapped_column(sa.DateTime(timezone=True), nullable=False)]
DateTime_Nullable = typing.Annotated[
    datetime.datetime | None, sa_orm.mapped_column(sa.DateTime(timezone=True), nullable=True)
]
Date = typing.Annotated[datetime.date, sa_orm.mapped_column(sa.Date, nullable=False)]
Date_Nullable = typing.Annotated[datetime.date | None, sa_orm.mapped_column(sa.Date, nullable=True)]

UserFK = typing.Annotated[uuid.UUID, sa_orm.mapped_column(sa.ForeignKey("user.uuid"), nullable=False, index=True)]
UserFK_Nullable = typing.Annotated[uuid.UUID | None, sa_orm.mapped_column(sa.ForeignKey("user.uuid"), nullable=True)]
FileFK = typing.Annotated[uuid.UUID, sa_orm.mapped_column(sa.ForeignKey("file.uuid"), nullable=False)]
FileFK_Nullable = typing.Annotated[uuid.UUID | None, sa_orm.mapped_column(sa.ForeignKey("file.uuid"), nullable=True)]

Json = typing.Annotated[dict, sa_orm.mapped_column(sa.JSON)]
Json_Nullable = typing.Annotated[dict | None, sa_orm.mapped_column(sa.JSON)]
