import typing

import fastapi
import sqlalchemy.ext.asyncio as sa_ext_asyncio

import redis
import src.config.fastapi
import src.db
import src.redis
import src.util.time_util


def fastapi_setting_di(request: fastapi.Request) -> typing.Generator[src.config.fastapi.FastAPISetting, None, None]:
    fastapi_app: fastapi.FastAPI = request.app
    config_obj: src.config.fastapi.FastAPISetting = fastapi_app.state.config_obj
    yield config_obj


async def async_db_session_di(request: fastapi.Request) -> typing.AsyncGenerator[sa_ext_asyncio.AsyncSession, None]:
    fastapi_app: fastapi.FastAPI = request.app
    async_db: src.db.AsyncDB = fastapi_app.state.async_db
    async with async_db.get_async_session() as session:
        yield session


async def async_redis_session_di(request: fastapi.Request) -> typing.AsyncGenerator[redis.Redis, None]:
    fastapi_app: fastapi.FastAPI = request.app
    async_redis: src.redis.AsyncRedis = fastapi_app.state.async_redis
    async with async_redis.get_async_session() as session:
        yield session


dbDI = typing.Annotated[sa_ext_asyncio.AsyncSession, fastapi.Depends(async_db_session_di)]
redisDI = typing.Annotated[redis.Redis, fastapi.Depends(async_redis_session_di)]
settingDI = typing.Annotated[src.config.fastapi.FastAPISetting, fastapi.Depends(fastapi_setting_di)]
