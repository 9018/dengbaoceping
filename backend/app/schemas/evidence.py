from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.asset import AssetRead
from app.schemas.common import TimestampSchema
from app.schemas.guidance import GuidanceItemRead


class EvidenceBase(BaseModel):
    asset_id: str | None = Field(default=None, description="关联文件资产ID")
    matched_asset_id: str | None = Field(default=None, description="匹配测试对象资产ID")
    matched_guidance_id: str | None = Field(default=None, description="匹配指导书条目ID")
    evidence_type: str = Field(..., description="证据类型")
    title: str = Field(..., description="证据标题")
    summary: str | None = Field(default=None, description="证据摘要")
    text_content: str | None = Field(default=None, description="证据正文或抽取文本")
    ocr_result_json: dict | list | None = Field(default=None, description="OCR结构化结果JSON")
    ocr_status: str | None = Field(default=None, description="OCR状态")
    ocr_provider: str | None = Field(default=None, description="OCR提供方")
    ocr_processed_at: datetime | None = Field(default=None, description="OCR处理时间")
    device: str | None = Field(default=None, description="关联设备名称")
    ports_json: dict | list | None = Field(default=None, description="端口或网络信息JSON")
    evidence_time: datetime | None = Field(default=None, description="证据时间")
    tags_json: dict | list | None = Field(default=None, description="证据标签JSON")
    source_ref: str | None = Field(default=None, description="来源引用标识")
    asset_match_score: float | None = Field(default=None, description="测试对象匹配得分")
    asset_match_reasons_json: dict | list | None = Field(default=None, description="测试对象匹配原因JSON")
    asset_match_status: str | None = Field(default=None, description="测试对象匹配状态")
    guidance_match_score: float | None = Field(default=None, description="指导书匹配得分")
    guidance_match_reasons_json: dict | list | None = Field(default=None, description="指导书匹配原因JSON")
    guidance_match_status: str | None = Field(default=None, description="指导书匹配状态")


class EvidenceCreate(EvidenceBase):
    project_id: str = Field(..., description="所属项目ID")


class EvidenceUploadData(BaseModel):
    title: str | None = Field(default=None, description="证据标题")
    evidence_type: str = Field(default="uploaded_file", description="证据类型")
    summary: str | None = Field(default=None, description="证据摘要")
    text_content: str | None = Field(default=None, description="证据正文或抽取文本")
    device: str | None = Field(default=None, description="关联设备名称")
    ports_json: dict | list | None = Field(default=None, description="端口或网络信息JSON")
    evidence_time: datetime | None = Field(default=None, description="证据时间")
    tags_json: dict | list | None = Field(default=None, description="证据标签JSON")
    source_ref: str | None = Field(default=None, description="来源引用标识")
    category: str = Field(default="evidence", description="文件分类标识")
    category_label: str = Field(default="证据文件", description="文件分类名称")


class EvidenceOCRRequest(BaseModel):
    sample_id: str | None = Field(default=None, description="mock OCR样例ID；paddle/real provider 场景下可为空且会被忽略")
    force: bool = Field(default=False, description="是否强制重新执行")


class EvidenceExtractRequest(BaseModel):
    template_code: str | None = Field(default=None, description="抽取模板编码")
    force: bool = Field(default=False, description="是否强制重新执行")


class EvidenceMatchAssetRequest(BaseModel):
    force: bool = Field(default=False, description="是否强制重新匹配")


class EvidenceConfirmAssetRequest(BaseModel):
    asset_id: str | None = Field(default=None, description="确认绑定的测试对象资产ID")


class EvidenceMatchGuidanceRequest(BaseModel):
    force: bool = Field(default=False, description="是否强制重新匹配指导书")


class EvidenceConfirmGuidanceRequest(BaseModel):
    guidance_id: str | None = Field(default=None, description="确认绑定的指导书条目ID")


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
    source_page: int | None
    source_sheet: str | None
    source_row: int | None
    rule_id: str | None

    model_config = ConfigDict(from_attributes=True)


class EvidenceUpdate(BaseModel):
    asset_id: str | None = None
    matched_asset_id: str | None = None
    matched_guidance_id: str | None = None
    evidence_type: str | None = None
    title: str | None = None
    summary: str | None = None
    text_content: str | None = None
    device: str | None = None
    ports_json: dict | list | None = None
    evidence_time: datetime | None = None
    tags_json: dict | list | None = None
    source_ref: str | None = None
    asset_match_score: float | None = None
    asset_match_reasons_json: dict | list | None = None
    asset_match_status: str | None = None
    guidance_match_score: float | None = None
    guidance_match_reasons_json: dict | list | None = None
    guidance_match_status: str | None = None


class EvidenceRead(EvidenceBase, TimestampSchema):
    id: str
    project_id: str
    matched_asset: AssetRead | None = None
    matched_guidance: GuidanceItemRead | None = None

    model_config = ConfigDict(from_attributes=True)
