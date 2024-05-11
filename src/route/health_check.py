import logging

import fastapi
import sqlalchemy as sa

import src.const.tag
import src.dependency.common as common_dep
import src.dependency.header as header_dep
import src.util.exception_util
import src.util.fastapi

logger = logging.getLogger(__name__)
router = fastapi.APIRouter(tags=[src.const.tag.OpenAPITag.HEALTH_CHECK])


class ReadyzResponse(src.util.fastapi.EmptyResponseSchema):
    debug: bool
    database: bool
    cache: bool


class AccessInfoResponse(src.util.fastapi.EmptyResponseSchema):
    user_agent: str
    user_ip: str


@router.get("/healthz", response_model=src.util.fastapi.EmptyResponseSchema, deprecated=True)
@router.get("/livez", response_model=src.util.fastapi.EmptyResponseSchema)
async def livez() -> dict[str, str]:
    return {"message": "ok"}


@router.get("/readyz", response_model=ReadyzResponse)
async def readyz(
    db_session: common_dep.dbDI, redis_session: common_dep.redisDI, config_obj: common_dep.settingDI
) -> dict[str, str | bool]:
    response: dict[str, str | bool] = {
        "message": "ok",
        "debug": config_obj.debug,
        "database": False,
        "cache": False,
    }

    try:
        await db_session.execute(sa.text("SELECT 1"))
        response["database"] = True
    except Exception as e:
        logger.exception("DB connection failed")
        logger.exception(src.util.exception_util.get_traceback_msg(e))

    try:
        response["cache"] = redis_session.ping()
    except Exception as e:
        logger.exception("Redis connection failed")
        logger.exception(src.util.exception_util.get_traceback_msg(e))
    return response


@router.get("/access_info", response_model=AccessInfoResponse)
async def access_info(
    user_ip: header_dep.user_ip = None,
    user_agent: header_dep.user_agent = None,
) -> dict[str, str | None]:
    return {"user_agent": user_agent, "user_ip": user_ip}
