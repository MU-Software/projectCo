from __future__ import annotations

import typing
import uuid

import fastapi
import fastapi.responses
import fastapi.security

import src.const.cookie
import src.const.error
import src.const.tag
import src.crud.authn_history
import src.crud.user as user_crud
import src.db.model.user as user_model
import src.dependency.authn as authn_dep
import src.dependency.common as common_dep
import src.dependency.header as header_dep
import src.schema.authn_history
import src.schema.user as user_schema
import src.util.fastapi
import src.util.fastapi.cookie

router = fastapi.APIRouter(tags=[src.const.tag.OpenAPITag.AUTHN], prefix="/authn")


@router.head(path="/csrf/")
async def set_csrf_token(
    response: fastapi.Response,
    setting: common_dep.settingDI,
    csrf_token: header_dep.csrf_token = None,
    force: bool = False,
) -> fastapi.responses.JSONResponse:
    if not csrf_token or force:
        src.util.fastapi.cookie.Cookie(
            **setting.to_cookie_config(),
            **src.const.cookie.CookieKey.CSRF_TOKEN.to_cookie_config(),
            value=str(uuid.uuid4()),
        ).set_cookie(response)
    response.status_code = 204
    return response


@router.post(path="/signup/", response_model=user_schema.UserDTO)
async def signup(db_session: common_dep.dbDI, payload: user_schema.UserCreate) -> user_model.User:
    return await user_crud.userCRUD.create(db_session, obj_in=payload)


@router.post(path="/signin/", response_model=user_schema.UserTokenResponse)
async def signin(
    db_session: common_dep.dbDI,
    config_obj: common_dep.settingDI,
    user_ip: header_dep.user_ip,
    user_agent: header_dep.user_agent,
    csrf_token: header_dep.csrf_token,
    payload: typing.Annotated[fastapi.security.OAuth2PasswordRequestForm, fastapi.Depends()],
    response: fastapi.Response,
) -> dict:
    user = await user_crud.userCRUD.signin(db_session, user_ident=payload.username, password=payload.password)
    refresh_token_obj = await src.crud.authn_history.userSignInHistoryCRUD.signin(
        session=db_session,
        obj_in=src.schema.authn_history.UserSignInHistoryCreate(
            user_uuid=user.uuid,
            ip=user_ip,
            user_agent=user_agent,
            config_obj=config_obj,
        ),
    )
    src.util.fastapi.cookie.Cookie(
        **src.const.cookie.CookieKey.REFRESH_TOKEN.to_cookie_config(),
        **config_obj.to_cookie_config(),
        value=refresh_token_obj.jwt,
        expires=refresh_token_obj.exp,
    ).set_cookie(response)
    response.status_code = 201
    return {"access_token": refresh_token_obj.to_access_token(csrf_token=csrf_token).jwt}


@router.delete(path="/signout/")
async def signout(
    db_session: common_dep.dbDI,
    redis_session: common_dep.redisDI,
    config_obj: common_dep.settingDI,
    access_token: authn_dep.access_token_di,
    response: fastapi.Response,
) -> fastapi.responses.Response:
    for cookie_key in (src.const.cookie.CookieKey.REFRESH_TOKEN, src.const.cookie.CookieKey.CSRF_TOKEN):
        kwargs = {**config_obj.to_cookie_config(), **cookie_key.to_cookie_config()}
        src.util.fastapi.cookie.Cookie.model_validate(kwargs).delete_cookie(response)

    await src.crud.authn_history.userSignInHistoryCRUD.delete(
        session=db_session,
        redis_session=redis_session,
        token=access_token,
    )

    response.status_code = 204
    return response


@router.put(path="/verify/", response_model=src.util.fastapi.EmptyResponseSchema)
async def verify(access_token: authn_dep.access_token_di) -> dict:
    return {"message": "ok"}


@router.get(path="/refresh/", response_model=user_schema.UserTokenResponse)
async def refresh(
    db_session: common_dep.dbDI,
    config_obj: common_dep.settingDI,
    csrf_token: header_dep.csrf_token,
    refresh_token: authn_dep.refresh_token_di,
    response: fastapi.Response,
) -> dict:
    refresh_token = await src.crud.authn_history.userSignInHistoryCRUD.refresh(session=db_session, token=refresh_token)

    src.util.fastapi.cookie.Cookie(
        **src.const.cookie.CookieKey.REFRESH_TOKEN.to_cookie_config(),
        **config_obj.to_cookie_config(),
        value=refresh_token.jwt,
        expires=refresh_token.exp,
    ).set_cookie(response)
    return {"access_token": refresh_token.to_access_token(csrf_token=csrf_token).jwt, "token_type": "bearer"}


@router.post(path="/update-password/", response_model=user_schema.UserDTO)
async def update_password(
    db_session: common_dep.dbDI,
    access_token: authn_dep.access_token_di,
    payload: user_schema.UserPasswordUpdate,
) -> user_model.User:
    return await user_crud.userCRUD.update_password(
        session=db_session,
        uuid=access_token.user,
        obj_in=payload,
    )


# TODO: Implement this
# @router.post(path="/reset-password/")
# async def reset_password(
#     db_session: common_dep.dbDI,
#     payload: user_schema.UserPasswordReset,
# ) -> None:
#     return await user_crud.userCRUD.reset_password(db_session, payload)
