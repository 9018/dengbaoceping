from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.common import TimestampSchema


class HistoryRecordRead(TimestampSchema):
    id: str
    source_file: str
    sheet_name: str
    asset_name: str
    asset_type: str | None
    extension_standard: str | None
    control_point: str | None
    evaluation_item: str | None
    record_text: str | None
    compliance_status: str | None
    score: float | None
    item_no: str | None
    row_index: int
    keywords_json: list[str]

    model_config = ConfigDict(from_attributes=True)


class HistoryGuidanceLinkRead(BaseModel):
    history_record_id: str
    guidance_item_id: str
    match_score: float
    match_reason: dict
    section_title: str
    section_path: str
    guidance_code: str


class HistoryImportRead(BaseModel):
    source_file: str
    sheet_count: int
    imported_count: int
    skipped_count: int
    compliance_status_counts: dict[str, int]


class HistoryStatsRead(BaseModel):
    sheet_count: int
    total: int
    compliance_status_counts: dict[str, int]
    asset_type_counts: dict[str, int]


class HistorySimilarRead(BaseModel):
    id: str
    sheet_name: str
    asset_name: str
    asset_type: str | None
    control_point: str | None
    evaluation_item: str | None
    compliance_status: str | None
    score: float
    reasons: list[str]


class HistoryPhraseSummaryRead(BaseModel):
    phrase: str
    total: int
    compliance_status_counts: dict[str, int]
