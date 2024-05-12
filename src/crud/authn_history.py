import redis
import src.const.error
import src.const.jwt
import src.const.redis
import src.crud.__interface__ as crud_interface
import src.db.__type__ as db_types
import src.db.model.user as user_model
import src.schema.authn_history
import src.schema.user as user_schema
import src.util.string_util
import src.util.time_util


class UserSignInHistoryCRUD(
    crud_interface.CRUDBase[
        user_model.UserSignInHistory,
        src.schema.authn_history.UserSignInHistoryCreate,
        crud_interface.EmptySchema,
    ]
):
    async def delete(  # type: ignore[override]
        self, session: db_types.As, redis_session: redis.Redis, token: user_schema.UserJWTToken
    ) -> None:
        if not (db_obj := await self.get_using_token_obj(session=session, token=token)):
            src.const.error.AuthNError.AUTH_HISTORY_NOT_FOUND().raise_()
        db_obj.deleted_at = db_obj.expires_at = src.util.time_util.get_utcnow()
        await session.commit()

        redis_key = src.const.redis.RedisKeyType.TOKEN_REVOKED.as_redis_key(str(token.user))
        redis_session.set(redis_key, "1", ex=src.const.jwt.UserJWTTokenType.refresh.value.expiration_delta)

    async def get_using_token_obj(
        self, session: db_types.As, token: user_schema.UserJWTToken
    ) -> user_model.UserSignInHistory:
        if not (db_obj := await self.get(session=session, uuid=token.jti)):
            src.const.error.AuthNError.AUTH_HISTORY_NOT_FOUND().raise_()
        return db_obj

    async def signin(
        self, session: db_types.As, obj_in: src.schema.authn_history.UserSignInHistoryCreate
    ) -> user_schema.RefreshToken:
        db_obj = await self.create(session=session, obj_in=obj_in)
        return user_schema.RefreshToken.from_orm(signin_history=db_obj, config_obj=obj_in.config_obj)

    async def refresh(self, session: db_types.As, token: user_schema.RefreshToken) -> user_schema.RefreshToken:
        if token.should_refresh:
            if not (db_obj := await self.get_using_token_obj(session=session, token=token)):
                src.const.error.AuthNError.AUTH_HISTORY_NOT_FOUND().raise_()
            new_expires_at = (
                src.util.time_util.get_utcnow() + src.const.jwt.UserJWTTokenType.refresh.value.expiration_delta
            )
            token.exp = db_obj.expires_at = new_expires_at
            await session.commit()
        return token


userSignInHistoryCRUD = UserSignInHistoryCRUD(model=user_model.UserSignInHistory)
