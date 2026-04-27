from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import TimestampSchema


class GuidanceItemUpdate(BaseModel):
    guidance_code: str | None = None
    section_path: str | None = None
    section_title: str | None = None
    level1: str | None = None
    level2: str | None = None
    level3: str | None = None
    raw_markdown: str | None = None
    plain_text: str | None = None
    keywords_json: list[str] | None = None
    check_points_json: list[str] | None = None
    evidence_requirements_json: list[str] | None = None
    record_suggestion: str | None = None


class GuidanceItemRead(TimestampSchema):
    id: str
    guidance_code: str
    source_file: str
    section_path: str
    section_title: str
    level1: str | None
    level2: str | None
    level3: str | None
    raw_markdown: str
    plain_text: str
    keywords_json: list[str]
    check_points_json: list[str]
    evidence_requirements_json: list[str]
    record_suggestion: str | None

    model_config = ConfigDict(from_attributes=True)


class GuidanceHistoryLinkRead(BaseModel):
    guidance_item_id: str
    history_record_id: str
    match_score: float
    match_reason: dict
    record_text: str | None
    compliance_status: str | None
    asset_type: str | None
    control_point: str | None
    evaluation_item: str | None
    sheet_name: str


class GuidanceEvidenceHistoryRead(BaseModel):
    history_record_id: str
    sheet_name: str
    asset_name: str | None
    asset_type: str | None
    compliance_status: str | None
    match_score: float
    match_reason: dict


class GuidanceMatchReasonsRead(BaseModel):
    summary: list[str] = []
    matched_guidance_id: str | None = None
    guidance_code: str | None = None
    section_title: str | None = None
    section_path: str | None = None
    score: float | None = None
    score_breakdown: dict | None = None
    signals: dict | None = None
    history_count: int = 0
    top_history: list[GuidanceEvidenceHistoryRead] = []
    confirmed_guidance_id: str | None = None
    confirmed_guidance_code: str | None = None
    confirmed_section_title: str | None = None


class GuidanceHistoryLinkResult(BaseModel):
    guidance_item_id: str
    linked_count: int
    updated_count: int
    top_score: float | None


class GuidanceLibraryStatus(BaseModel):
    source_file: str
    absolute_path: str
    file_exists: bool
    file_empty: bool
    file_message: str
    imported: bool
    total: int


class GuidanceLibraryRead(GuidanceLibraryStatus):
    keyword: str | None = None
    items: list[GuidanceItemRead]


class GuidanceImportRead(GuidanceLibraryStatus):
    batch_id: str | None = None
    source_file_hash: str | None = None
    imported_count: int
    updated_count: int = 0
    skipped_count: int = 0
    deleted_count: int = 0
    duplicate: bool = False
    duplicate_of_id: str | None = None
    status: str | None = None
