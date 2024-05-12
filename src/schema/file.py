from __future__ import annotations

import datetime
import functools
import mimetypes
import typing
import urllib.parse
import uuid

import pydantic

import src.const.time
import src.util.file_util
import src.util.string_util
import src.util.time_util

ResponseCacheControlType = typing.Literal[
    "no-cache",
    "no-store",
    "no-transform",
    "must-revalidate",
    "proxy-revalidate",
    "must-understand",
    "private",
    "public",
    "immutable",
]


class FileInfoDTO(pydantic.BaseModel):
    uuid: uuid.UUID

    path: pydantic.FilePath = pydantic.Field(exclude=True)
    mimetype: str | None
    hash: str
    size: int
    created_at: datetime.datetime
    modified_at: datetime.datetime

    model_config = pydantic.ConfigDict(from_attributes=True)

    @pydantic.computed_field  # type: ignore[misc]
    @property
    def filename(self) -> str:
        return self.path.name


class FileMetadataDTO(pydantic.BaseModel):
    content_range: range | None = None

    path: pydantic.FilePath = pydantic.Field(exclude=True, validation_alias="path")
    size: int = pydantic.Field(exclude=True, validation_alias="size")
    hash: str = pydantic.Field(validation_alias="hash", serialization_alias="ETag", alias_priority=2)
    mimetype: str = pydantic.Field(validation_alias="mimetype", serialization_alias="Content-Type", alias_priority=2)
    modified_at: datetime.datetime = pydantic.Field(
        validation_alias="modified_at",
        serialization_alias="Last-Modified",
        alias_priority=2,
    )

    accept_ranges: typing.Literal["bytes"] = "bytes"
    cache_control: list[ResponseCacheControlType] = ["no-cache"]

    model_config = pydantic.ConfigDict(
        alias_generator=src.util.string_util.snake_to_train_case,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )

    @pydantic.model_validator(mode="after")
    def validate(self) -> typing.Self:
        if self.content_range:
            if self.content_range.start >= self.size:
                raise ValueError("content_range.start must be less than size")
            if self.content_range.stop and self.content_range.stop > self.size:
                raise ValueError("content_range.stop must be less than size")
            if self.content_range.start >= self.content_range.stop:
                raise ValueError("content_range.start must be less than content_range.stop")
            if self.content_range.step:
                raise ValueError("content_range.step must be None")

        return self

    @pydantic.field_serializer("modified_at", when_used="always")
    def serialize_modified_at(self, value: datetime.datetime) -> str:
        return src.util.time_util.as_utctime(value).strftime(src.const.time.RFC_7231_GMT_DATETIME_FORMAT)

    @pydantic.field_serializer("cache_control", when_used="always")
    def serialize_cache_control(self, value: list[ResponseCacheControlType]) -> str:
        return ", ".join(value)

    @pydantic.field_serializer("content_range", when_used="always")
    def serialize_content_range(self, value: range | None = None) -> str:
        if not value:
            return f"bytes */{self.size}"
        return f"bytes {value.start}-{value.stop or self.size - 1}/{self.size}"

    @pydantic.computed_field  # type: ignore[misc]
    @property
    def content_disposition(self) -> str:
        encoded_filename = urllib.parse.quote(self.path.name, encoding="utf-8")
        return f'attachment; filename="{encoded_filename}"'

    def model_dump_as_download_header(self) -> dict[str, str]:
        return self.model_dump(by_alias=True, exclude_none=True)

    def model_dump_as_preview_header(self) -> dict[str, str]:
        return self.model_dump(by_alias=True, exclude_none=True) | {"Content-Disposition": "inline"}

    def model_dump_as_head_header(self) -> dict[str, str]:
        return self.model_dump(by_alias=True, exclude_none=True, exclude={"mimetype", "content_disposition"})


class FileCreate(pydantic.BaseModel):
    path: pydantic.FilePath
    data: pydantic.Json | None = None

    private: bool = False
    readable: bool = True
    writable: bool = False
    created_by_uuid: uuid.UUID

    @pydantic.computed_field  # type: ignore[misc]
    @functools.cached_property
    def mimetype(self) -> str | None:
        return mimetypes.guess_type(self.path)[0]

    @pydantic.computed_field  # type: ignore[misc]
    @functools.cached_property
    def hash(self) -> str:
        return src.util.file_util.file_md5(self.path)

    @pydantic.computed_field  # type: ignore[misc]
    @functools.cached_property
    def size(self) -> int:
        return (self.path).stat().st_size


class FileUpdate(pydantic.BaseModel):
    data: pydantic.Json | None = None
    private: bool = False
    readable: bool = True
    writable: bool = False
