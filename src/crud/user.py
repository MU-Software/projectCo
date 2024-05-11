import contextlib
import uuid

import argon2
import sqlalchemy as sa

import src.const.error
import src.const.jwt
import src.const.redis
import src.crud.__interface__ as crud_interface
import src.db.__type__ as db_types
import src.db.model.user as user_model
import src.schema.user as user_schema
import src.util.string_util
import src.util.time_util


class UserCRUD(crud_interface.CRUDBase[user_model.User, user_schema.UserCreate, user_schema.UserUpdate]):
    async def signin(self, session: db_types.As, user_ident: str, password: str) -> user_model.User:
        if user_ident.startswith("@"):
            column, user_ident = user_model.User.username, user_ident[1:]
        elif "@" in user_ident and src.util.string_util.is_email(user_ident):
            column, user_ident = user_model.User.email, user_ident
        else:
            column, user_ident = user_model.User.username, user_ident

        stmt = sa.select(self.model).where(column == user_ident)

        if not (user := await session.scalar(stmt)):
            src.const.error.AuthNError.SIGNIN_USER_NOT_FOUND().raise_()
        elif error_msg := user.signin_disabled_reason_message:
            src.const.error.AuthNError.SIGNIN_FAILED(msg=error_msg, input=user_ident).raise_()

        with contextlib.suppress(argon2.exceptions.VerifyMismatchError):
            argon2.PasswordHasher().verify(user.password, password)
            user.mark_as_signin_succeed()
            return await crud_interface.commit_and_return(session=session, db_obj=user)

        user.mark_as_signin_failed()
        await session.commit()

        default_err_msg = user_model.SignInDisabledReason.WRONG_PASSWORD.value.format(**user.dict)
        error_msg = user.signin_disabled_reason_message or default_err_msg
        src.const.error.AuthNError.SIGNIN_FAILED(msg=error_msg, input=user_ident).raise_()

    async def update_password(
        self, session: db_types.As, uuid: uuid.UUID, obj_in: user_schema.UserPasswordUpdate
    ) -> user_model.User:
        if not (user := await self.get(session=session, uuid=uuid)):
            src.const.error.AuthNError.AUTH_USER_NOT_FOUND().raise_()

        user.set_password(
            user_schema.UserPasswordUpdateForModel.model_validate_with_orm(
                orm_obj=user,
                data=obj_in.model_dump(),
            ).new_password,
        )
        return await crud_interface.commit_and_return(session=session, db_obj=user)


userCRUD = UserCRUD(model=user_model.User)
