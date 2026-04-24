from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampSchema


class ExportCreateRequest(BaseModel):
    format: str = Field(default="txt", description="导出格式")


class ExportJobRead(TimestampSchema):
    id: str
    project_id: str
    format: str
    status: str
    file_name: str
    file_size: int
    record_count: int

    model_config = ConfigDict(from_attributes=True)


class ExportPreviewRead(BaseModel):
    content: str
