from __future__ import annotations

import re

import psycopg.errors as pg_exc
import sqlalchemy.exc as sa_exc

import src.const.error
import src.db.__mixin__ as db_mixin
import src.error_handler.__type__ as err_type

IntegrityErrorMsgMap: dict[db_mixin.NCKey, src.const.error.ErrorStruct] = {
    "ix": src.const.error.DBServerError.DB_INTEGRITY_CONSTRAINT_ERROR(),
    "uq": src.const.error.DBValueError.DB_UNIQUE_CONSTRAINT_ERROR(),
    "ck": src.const.error.DBValueError.DB_CHECK_CONSTRAINT_ERROR(),
    "fk": src.const.error.DBValueError.DB_FOREIGN_KEY_CONSTRAINT_ERROR(),
    "pk": src.const.error.DBValueError.DB_NOT_NULL_CONSTRAINT_ERROR(),
}


def error_to_nckey(msg_primary: str) -> tuple[db_mixin.NCKey | None, re.Match | None]:
    if not isinstance(msg_primary, str):
        return None, None
    for nckey, ncdef in db_mixin.NAMING_CONVENTION_DICT.items():
        if matched_info := ncdef.regex.match(msg_primary):
            return nckey, matched_info
    return None, None


async def psycopg_dataerror_handler(req: err_type.ReqType, err: pg_exc.DataError) -> err_type.RespType:
    # TODO: FIXME: THis sould be handled by CRUDBase or CRUDView.
    # [print(attr, getattr(err.diag, attr)) for attr in dir(err.diag) if not attr.startswith("_")]
    return src.const.error.DBValueError.DB_DATA_ERROR().response()


async def psycopg_integrityerror_handler(req: err_type.ReqType, err: pg_exc.IntegrityError) -> err_type.RespType:
    # TODO: FIXME: THis sould be handled by CRUDBase or CRUDView.
    match err:
        case pg_exc.IntegrityConstraintViolation():
            return src.const.error.DBServerError.DB_INTEGRITY_CONSTRAINT_ERROR().response()
        case pg_exc.RestrictViolation():
            return src.const.error.DBValueError.DB_RESTRICT_CONSTRAINT_ERROR().response()
        case pg_exc.NotNullViolation():
            return src.const.error.DBValueError.DB_NOT_NULL_CONSTRAINT_ERROR().response()
        case pg_exc.ForeignKeyViolation():
            parsed_error = src.const.error.DBValueError.DB_NOT_NULL_CONSTRAINT_ERROR()
            err_msg = parsed_error.msg.format(referred_table_name=err.diag.table_name or "")
            return parsed_error(msg=err_msg).response()
        case pg_exc.UniqueViolation():
            return src.const.error.DBValueError.DB_UNIQUE_CONSTRAINT_ERROR().response()
        case pg_exc.CheckViolation():
            return src.const.error.DBValueError.DB_CHECK_CONSTRAINT_ERROR().response()
        case pg_exc.ExclusionViolation():
            return src.const.error.DBValueError.DB_EXCLUSION_CONSTRAINT_ERROR().response()
        case _:
            nc_key, _ = error_to_nckey(err.diag.message_primary)
            return IntegrityErrorMsgMap.get(nc_key, src.const.error.DBServerError.DB_UNKNOWN_ERROR())


async def psycopg_databaseerror_handler(req: err_type.ReqType, err: pg_exc.DatabaseError) -> err_type.RespType:
    if handler_func := error_handler_patterns.get(type(err)):
        return await handler_func(req, err)
    return src.const.error.DBServerError.DB_UNKNOWN_ERROR().response()


async def psycopg_connectionerror_handler(req: err_type.ReqType, err: pg_exc.Error) -> err_type.RespType:
    return src.const.error.DBServerError.DB_CONNECTION_ERROR().response()


async def psycopg_criticalerror_handler(req: err_type.ReqType, err: pg_exc.Error) -> err_type.RespType:
    return src.const.error.DBServerError.DB_CRITICAL_ERROR().response()


async def sqlalchemy_error_handler(req: err_type.ReqType, err: sa_exc.SQLAlchemyError) -> err_type.RespType:
    orig_exception: pg_exc.Error | BaseException | None  # For sa_exc.IntegrityError
    if orig_exception := getattr(err, "orig", None):
        for orig_err_type in type(orig_exception).__mro__:
            if handler_func := error_handler_patterns.get(orig_err_type):
                return await handler_func(req, orig_exception)
    return src.const.error.DBServerError.DB_UNKNOWN_ERROR().response()


error_handler_patterns = {
    # PostgreSQL Connection Error
    pg_exc.InterfaceError: psycopg_connectionerror_handler,
    pg_exc.CannotConnectNow: psycopg_connectionerror_handler,
    # PostgreSQL Critical Error
    pg_exc.DataCorrupted: psycopg_criticalerror_handler,
    pg_exc.IndexCorrupted: psycopg_criticalerror_handler,
    pg_exc.DiskFull: psycopg_criticalerror_handler,
    pg_exc.OutOfMemory: psycopg_criticalerror_handler,
    pg_exc.TooManyArguments: psycopg_criticalerror_handler,
    pg_exc.TooManyColumns: psycopg_criticalerror_handler,
    pg_exc.ConfigFileError: psycopg_criticalerror_handler,
    pg_exc.InvalidPassword: psycopg_criticalerror_handler,
    pg_exc.AdminShutdown: psycopg_criticalerror_handler,
    pg_exc.CrashShutdown: psycopg_criticalerror_handler,
    pg_exc.DatabaseDropped: psycopg_criticalerror_handler,
    pg_exc.SystemError: psycopg_criticalerror_handler,
    pg_exc.IoError: psycopg_criticalerror_handler,
    pg_exc.UndefinedFile: psycopg_criticalerror_handler,
    pg_exc.DuplicateFile: psycopg_criticalerror_handler,
    # PostgreSQL Integrity Error
    pg_exc.IntegrityConstraintViolation: psycopg_integrityerror_handler,
    pg_exc.RestrictViolation: psycopg_integrityerror_handler,
    pg_exc.NotNullViolation: psycopg_integrityerror_handler,
    pg_exc.ForeignKeyViolation: psycopg_integrityerror_handler,
    pg_exc.UniqueViolation: psycopg_integrityerror_handler,
    pg_exc.CheckViolation: psycopg_integrityerror_handler,
    pg_exc.ExclusionViolation: psycopg_integrityerror_handler,
    # PostgreSQL Data Error
    pg_exc.DataError: psycopg_dataerror_handler,
    # PostgreSQL Database Error
    pg_exc.Error: psycopg_databaseerror_handler,
    # SQLAlchemy Error
    sa_exc.SQLAlchemyError: sqlalchemy_error_handler,
}
