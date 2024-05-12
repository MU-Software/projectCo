import contextlib
import logging
import typing

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_ext_asyncio
import sqlalchemy.orm as sa_orm

import src.db.__mixin__ as db_mixin
import src.db.__type__ as db_type
import src.util.type_util

logger = logging.getLogger(__name__)


class DBConfigDescriptor(typing.Protocol):
    class SQLAlchemyConfigDescriptor(typing.Protocol):
        def to_sqlalchemy_config(self) -> dict[str, typing.Any]: ...

    debug: bool
    sqlalchemy: SQLAlchemyConfigDescriptor


class DB:
    config_obj: DBConfigDescriptor
    engine: sa.Engine | sa_ext_asyncio.AsyncEngine | None = None
    session_maker: (
        None
        | sa_orm.session.sessionmaker[sa_orm.Session]
        | sa_ext_asyncio.async_sessionmaker[sa_ext_asyncio.AsyncSession]
    ) = None

    def check_connection(self, session: db_type.Ps) -> None:
        """Check if DB is connected"""
        try:
            session.execute(sa.text("SELECT 1"))
        except Exception as e:
            logger.critical(f"DB connection failed: {e}")
            raise e

    def create_all_tables(self, session: db_type.Ps) -> None:
        """Create all tables only IF NOT EXISTS on debug mode"""
        if self.config_obj.debug:
            db_mixin.DefaultModelMixin.metadata.create_all(bind=self.engine.engine, checkfirst=True)


class SyncDB(DB, src.util.type_util.SyncConnectedResource):
    engine: sa.Engine | None = None
    session_maker: sa_orm.session.sessionmaker[sa_orm.Session] | None = None

    def open(self) -> typing.Self:
        # Create DB engine and session pool.
        config = self.config_obj.sqlalchemy.to_sqlalchemy_config()

        if not self.engine:
            self.engine = sa.engine_from_config(configuration=config, prefix="")
        if not self.session_maker:
            self.session_maker = sa_orm.session.sessionmaker(self.engine, autoflush=False, expire_on_commit=False)

        with self.session_maker() as session:
            self.check_connection(session)
            self.create_all_tables(session)

        return self

    def close(self) -> None:
        # Close DB engine and session pool.
        if self.session_maker:
            self.session_maker = None
        if self.engine:
            self.engine.dispose()
            self.engine = None

    @contextlib.contextmanager
    def get_sync_session(self) -> typing.Generator[sa_orm.Session, None, None]:
        if not self.session_maker:
            raise RuntimeError("DB is not opened")
        with self.session_maker() as session:
            try:
                yield session
                session.commit()
            except Exception as se:
                session.rollback()
                raise se
            finally:
                session.close()


class AsyncDB(DB, src.util.type_util.AsyncConnectedResource):
    engine: sa_ext_asyncio.AsyncEngine | None = None
    session_maker: sa_ext_asyncio.async_sessionmaker[sa_ext_asyncio.AsyncSession] | None = None

    async def aopen(self) -> typing.Self:
        # Create DB engine and session pool.
        config = self.config_obj.sqlalchemy.to_sqlalchemy_config()
        if not self.engine:
            self.engine = sa_ext_asyncio.async_engine_from_config(configuration=config, prefix="")
        if not self.session_maker:
            self.session_maker = sa_ext_asyncio.async_sessionmaker(self.engine, autoflush=False, expire_on_commit=False)

        async with self.session_maker() as session:
            await session.run_sync(self.check_connection)
            await session.run_sync(self.create_all_tables)

        return self

    async def aclose(self) -> None:
        # Close DB engine and session pool.
        if self.session_maker:
            self.session_maker = None
        if self.engine:
            await self.engine.dispose()
            self.engine = None

    @contextlib.asynccontextmanager
    async def get_async_session(self) -> typing.AsyncGenerator[sa_ext_asyncio.AsyncSession, None]:
        if not self.session_maker:
            raise RuntimeError("DB is not opened")
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as se:
                await session.rollback()
                raise se
            finally:
                await session.close()
