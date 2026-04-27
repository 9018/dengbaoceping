from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageSchema(BaseModel):
    message: str


class ErrorSchema(BaseModel):
    code: str
    message: str
    details: Any = None


class MetaSchema(BaseModel):
    total: int
    page: int | None = None
    page_size: int | None = None


class PageResult(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int


class ApiResponse(BaseModel):
    success: bool
    message: str | None = None
    data: Any = None
    meta: MetaSchema | None = None
    error: ErrorSchema | None = None


def success_response(data: Any = None, message: str = "ok") -> ApiResponse:
    return ApiResponse(success=True, message=message, data=jsonable_encoder(data))


def list_response(data: list[Any], message: str = "ok") -> ApiResponse:
    return ApiResponse(
        success=True,
        message=message,
        data=jsonable_encoder(data),
        meta=MetaSchema(total=len(data)),
    )


def paged_response(items: list[Any], total: int, page: int, page_size: int, message: str = "ok") -> ApiResponse:
    return ApiResponse(
        success=True,
        message=message,
        data=jsonable_encoder(PageResult(items=items, total=total, page=page, page_size=page_size)),
        meta=MetaSchema(total=total, page=page, page_size=page_size),
    )


def error_response(code: str, message: str, details: Any = None) -> ApiResponse:
    return ApiResponse(success=False, error=ErrorSchema(code=code, message=message, details=details))
