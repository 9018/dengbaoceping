from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampSchema


class FieldUpdateRequest(BaseModel):
    raw_value: str | None = None
    corrected_value: str | None = None
    confidence: float | None = None
    source_text: str | None = None
    status: str | None = None
    review_comment: str | None = None
    reviewed_by: str | None = None


class FieldReviewRequest(BaseModel):
    status: str = Field(..., description="复核状态")
    corrected_value: str | None = Field(default=None, description="纠正后值")
    review_comment: str | None = Field(default=None, description="复核意见")
    reviewed_by: str | None = Field(default=None, description="复核人")


class ExtractedFieldRead(TimestampSchema):
    id: str
    evidence_id: str | None
    field_group: str
    field_name: str
    raw_value: str | None
    corrected_value: str | None
    source_text: str | None
    confidence: float | None
    status: str | None
    review_comment: str | None
    reviewed_by: str | None
    reviewed_at: datetime | None
    source_page: int | None
    source_sheet: str | None
    source_row: int | None
    rule_id: str | None

    model_config = ConfigDict(from_attributes=True)
