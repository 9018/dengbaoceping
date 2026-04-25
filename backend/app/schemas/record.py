from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampSchema


class RecordGenerationHistoryRecord(BaseModel):
    id: str | None = None
    asset_name: str | None = None
    asset_type: str | None = None
    record_text: str | None = None
    raw_text: str | None = None
    compliance_result: str | None = None
    compliance_status: str | None = None
    control_point: str | None = None
    item_text: str | None = None
    evaluation_item: str | None = None
    match_score: float | None = None


class RecordGenerationInput(BaseModel):
    asset_name: str
    asset_type: str | None = None
    page_type: str | None = None
    matched_item: dict | None = None
    extracted_facts: dict[str, str | int | float | bool | list | dict | None] = Field(default_factory=dict)
    similar_history_records: list[RecordGenerationHistoryRecord] = Field(default_factory=list)


class RecordGenerationResult(BaseModel):
    record_text: str
    compliance_result: str
    confidence: float
    evidence_summary: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)


class RecordGenerateRequest(BaseModel):
    evidence_id: str = Field(..., description="证据ID")
    device_type_override: str | None = Field(default=None, description="设备类型覆盖值")
    selected_item_code: str | None = Field(default=None, description="人工选择的测评项编码")
    selected_template_code: str | None = Field(default=None, description="人工选择的模板编码")
    force_regenerate: bool = Field(default=False, description="是否强制重新生成")


class RecordUpdateRequest(BaseModel):
    record_content: str | None = None
    final_content: str | None = None
    status: str | None = None
    review_comment: str | None = None
    reviewed_by: str | None = None


class RecordReviewRequest(BaseModel):
    status: str = Field(..., description="复核状态")
    final_content: str | None = Field(default=None, description="最终确认内容")
    review_comment: str | None = Field(default=None, description="复核意见")
    reviewed_by: str | None = Field(default=None, description="复核人")


class RecordRead(TimestampSchema):
    id: str
    project_id: str
    asset_id: str | None
    evidence_ids: list[str]
    title: str | None
    record_content: str | None
    final_content: str | None
    matched_fields_json: dict | list | None
    match_candidates: dict | list | None
    status: str
    review_comment: str | None
    reviewed_by: str | None
    reviewed_at: datetime | None
    match_score: float | None
    match_reasons: dict | list | None
    template_code: str | None
    item_code: str | None
    conclusion: str | None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if hasattr(obj, "record_text"):
            payload = {
                "id": obj.id,
                "project_id": obj.project_id,
                "asset_id": obj.asset_id,
                "evidence_ids": [link.evidence_id for link in getattr(obj, "evidence_links", [])],
                "title": obj.title,
                "record_content": obj.record_text,
                "final_content": obj.final_content,
                "matched_fields_json": obj.matched_fields_json,
                "match_candidates": obj.match_candidates_json,
                "status": obj.status,
                "review_comment": obj.review_comment,
                "reviewed_by": obj.reviewed_by,
                "reviewed_at": obj.reviewed_at,
                "match_score": obj.match_score,
                "match_reasons": obj.match_reasons_json,
                "template_code": obj.template_code,
                "item_code": obj.item_code,
                "conclusion": obj.conclusion,
                "created_at": obj.created_at,
                "updated_at": obj.updated_at,
            }
            return super().model_validate(payload, *args, **kwargs)
        return super().model_validate(obj, *args, **kwargs)
