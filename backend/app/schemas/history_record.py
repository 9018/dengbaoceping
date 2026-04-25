from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.common import TimestampSchema


class HistoryRecordRead(TimestampSchema):
    id: str
    source_file: str
    project_name: str | None = None
    sheet_name: str
    asset_name: str
    asset_type: str | None
    asset_ip: str | None = None
    asset_version: str | None = None
    standard_type: str | None = None
    extension_standard: str | None
    control_point: str | None
    item_text: str | None = None
    evaluation_item: str | None
    record_text: str | None
    raw_text: str | None = None
    compliance_result: str | None = None
    compliance_status: str | None
    score_weight: float | None = None
    score: float | None
    item_code: str | None = None
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
    source_file: str | None = None
    project_name: str | None = None
    sheet_name: str
    asset_name: str
    asset_type: str | None
    asset_ip: str | None = None
    asset_version: str | None = None
    standard_type: str | None = None
    control_point: str | None
    item_text: str | None = None
    evaluation_item: str | None = None
    record_text: str | None = None
    raw_text: str | None = None
    compliance_result: str | None = None
    compliance_status: str | None = None
    score_weight: float | None = None
    item_code: str | None = None
    score: float
    reasons: list[str]


class HistoricalAssessmentSimilarSearchRequest(BaseModel):
    ocr_text: str | None = None
    asset_type: str | None = None
    page_type: str | None = None
    control_point: str | None = None
    item_text: str | None = None


HistoricalAssessmentRecordRead = HistoryRecordRead
HistoricalAssessmentImportRead = HistoryImportRead
HistoricalAssessmentSimilarRead = HistorySimilarRead


class HistoryPhraseSummaryRead(BaseModel):
    phrase: str
    total: int
    compliance_status_counts: dict[str, int]
