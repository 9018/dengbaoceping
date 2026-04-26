from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.common import TimestampSchema
from app.schemas.guidance import GuidanceItemRead
from app.schemas.history_record import HistoryRecordRead


class AssessmentTemplateImportRead(BaseModel):
    workbook_id: str
    source_file: str
    name: str
    version: str | None = None
    sheet_count: int
    sheet_names: list[str]
    item_count: int
    imported_count: int
    skipped_count: int


class AssessmentTemplateWorkbookRead(TimestampSchema):
    id: str
    source_file: str
    name: str
    version: str | None = None
    sheet_count: int
    item_count: int

    model_config = ConfigDict(from_attributes=True)


class AssessmentTemplateStatsRead(BaseModel):
    object_type_counts: dict[str, int]
    object_category_counts: dict[str, int]
    control_point_counts: dict[str, int]


class AssessmentTemplateWorkbookDetailRead(AssessmentTemplateWorkbookRead):
    object_type_counts: dict[str, int]
    object_category_counts: dict[str, int]
    control_point_counts: dict[str, int]


class AssessmentTemplateSheetRead(TimestampSchema):
    id: str
    workbook_id: str
    sheet_name: str
    object_type: str | None = None
    object_category: str | None = None
    object_subtype: str | None = None
    is_physical: bool
    is_network: bool
    is_security_device: bool
    is_server: bool
    is_database: bool
    is_middleware: bool
    is_application: bool
    is_data_object: bool
    is_management: bool
    row_count: int

    model_config = ConfigDict(from_attributes=True)


class AssessmentTemplateItemRead(TimestampSchema):
    id: str
    workbook_id: str
    sheet_id: str
    sheet_name: str
    row_index: int
    standard_type: str | None = None
    control_point: str | None = None
    item_text: str | None = None
    record_template: str | None = None
    default_compliance_result: str | None = None
    weight: float | None = None
    item_code: str | None = None
    object_type: str | None = None
    object_category: str | None = None
    page_types_json: list[str] | dict | None = None
    required_facts_json: list[str] | dict | None = None
    evidence_keywords_json: list[str] | dict | None = None
    command_keywords_json: list[str] | dict | None = None
    applicability_json: list[str] | dict | None = None
    raw_row_json: dict | list | None = None

    model_config = ConfigDict(from_attributes=True)


class TemplateGuidebookLinkResultRead(BaseModel):
    template_item_id: str
    linked_count: int
    updated_count: int
    top_score: float | None = None


class TemplateGuidebookLinkRead(BaseModel):
    template_item_id: str
    guidance_item_id: str
    match_score: float
    match_reason: dict
    guidance_item: GuidanceItemRead
    section_title: str
    section_path: str
    guidance_code: str
    check_points: list[str]
    evidence_requirements: list[str]
    record_suggestion: str | None = None


class TemplateHistoryLinkResultRead(BaseModel):
    template_item_id: str
    linked_count: int
    updated_count: int
    top_score: float | None = None


class TemplateHistoryLinkRead(BaseModel):
    template_item_id: str
    history_record_id: str
    match_score: float
    match_reason: dict
    history_record: HistoryRecordRead
    sheet_name: str
    asset_name: str
    asset_type: str | None = None
    control_point: str | None = None
    item_text: str | None = None
    evaluation_item: str | None = None
    record_text: str | None = None
    raw_text: str | None = None
    compliance_result: str | None = None
    compliance_status: str | None = None
