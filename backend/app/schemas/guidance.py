from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import TimestampSchema


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
    imported_count: int
