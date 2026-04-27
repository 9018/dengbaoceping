from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampSchema


class ProjectBase(BaseModel):
    code: str | None = Field(default=None, description="项目编码")
    name: str = Field(..., description="项目名称")
    project_type: str = Field(default="等级保护测评", description="项目类型")
    status: str = Field(default="draft", description="项目状态")
    description: str | None = Field(default=None, description="项目说明")
    storage_root: str | None = Field(default=None, description="项目存储根目录")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    project_type: str | None = None
    status: str | None = None
    description: str | None = None
    storage_root: str | None = None


class ProjectTemplateImportRead(BaseModel):
    template_id: str
    source_asset_id: str
    source_file: str
    sheet_count: int
    sheet_names: list[str]
    imported_count: int
    skipped_count: int


class ProjectTemplateSummaryRead(TimestampSchema):
    template_id: str
    project_id: str
    name: str
    template_type: str
    version: str | None = None
    source_asset_id: str | None = None
    source_file: str | None = None
    sheet_count: int
    sheet_names: list[str]
    item_count: int
    is_active: bool


class ProjectRead(ProjectBase, TimestampSchema):
    id: str

    model_config = ConfigDict(from_attributes=True)


class ProjectAssessmentTableRead(TimestampSchema):
    id: str
    project_id: str
    asset_id: str
    source_workbook_id: str | None = None
    name: str
    status: str
    item_count: int

    model_config = ConfigDict(from_attributes=True)


class ProjectAssessmentItemRead(TimestampSchema):
    id: str
    table_id: str
    project_id: str
    asset_id: str
    source_template_item_id: str | None = None
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
    evidence_ids_json: list[str] | dict | None = None
    evidence_facts_json: list[dict] | dict | None = None
    guidance_refs_json: list[dict] | dict | None = None
    history_refs_json: list[dict] | dict | None = None
    draft_record_text: str | None = None
    draft_compliance_result: str | None = None
    final_record_text: str | None = None
    final_compliance_result: str | None = None
    confidence: float | None = None
    match_score: float | None = None
    match_reason_json: dict | list | None = None
    status: str
    review_comment: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


WorkflowStage = Literal[
    "global_template_missing",
    "guidance_missing",
    "history_missing",
    "asset_missing",
    "table_missing",
    "evidence_missing",
    "ocr_pending",
    "facts_missing",
    "item_match_missing",
    "draft_missing",
    "confirm_missing",
    "next_item",
    "completed",
]

WorkflowStepKey = Literal[
    "setup",
    "asset",
    "table",
    "evidence",
    "ocr",
    "facts",
    "match",
    "draft",
    "confirm",
    "export",
]


class WorkflowProjectStatsRead(BaseModel):
    asset_count: int = 0
    table_count: int = 0
    item_count: int = 0
    evidence_count: int = 0
    ocr_completed_count: int = 0
    fact_count: int = 0
    matched_item_count: int = 0
    drafted_item_count: int = 0
    confirmed_item_count: int = 0
    pending_item_count: int = 0
    pending_review_count: int = 0


class WorkflowNextActionRead(BaseModel):
    project_id: str
    stage: WorkflowStage
    step_key: WorkflowStepKey
    step_index: int
    route: str
    message: str
    table_id: str | None = None
    item_id: str | None = None
    asset_id: str | None = None
    evidence_id: str | None = None
    stats: WorkflowProjectStatsRead


class WorkflowProjectStatusRead(BaseModel):
    project_id: str
    status: WorkflowStage
    canNext: bool
    summary: str
    table_count: int
    item_count: int
    next_action: WorkflowNextActionRead
    stats: WorkflowProjectStatsRead
