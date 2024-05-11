from __future__ import annotations

import typing
import uuid

import fastapi
import fastapi.responses
import fastapi.security
import sqlalchemy as sa

import src.const.cookie
import src.const.error
import src.const.tag
import src.crud.authn_history
import src.db.model.user as user_model
import src.dependency.authn as authn_dep
import src.dependency.common as common_dep
import src.schema.authn_history
import src.util.fastapi
import src.util.fastapi.cookie

router = fastapi.APIRouter(tags=[src.const.tag.OpenAPITag.AUTHN_SIGNIN_HISTORY], prefix="/authn/history")


@router.get(path="/", response_model=list[src.schema.authn_history.UserSignInHistoryDTO])
async def get_signin_history(
    db_session: common_dep.dbDI, access_token: authn_dep.access_token_di
) -> typing.Iterable[user_model.UserSignInHistory]:
    stmt = sa.select(user_model.UserSignInHistory).where(
        user_model.UserSignInHistory.user_uuid == access_token.user,
        user_model.UserSignInHistory.expires_at.is_(None),
        user_model.UserSignInHistory.deleted_at.is_(None),
    )
    return await src.crud.authn_history.userSignInHistoryCRUD.get_multi_using_query(db_session, stmt)


@router.delete(path="/{usih_uuid}")
async def revoke_signin_history(
    db_session: common_dep.dbDI,
    redis_session: common_dep.redisDI,
    access_token: authn_dep.access_token_di,
    usih_uuid: uuid.UUID,
    response: fastapi.Response,
) -> None:
    if access_token.jti == usih_uuid:
        src.const.error.AuthNError.SELF_REVOKE_NOT_ALLOWED().raise_()

    await src.crud.authn_history.userSignInHistoryCRUD.delete(
        session=db_session,
        redis_session=redis_session,
        token=access_token,
    )
    response.status_code = 204
