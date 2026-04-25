from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Evidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evidences"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属项目ID")
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联文件资产ID")
    matched_asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True, comment="匹配测试对象资产ID")
    matched_guidance_id: Mapped[str | None] = mapped_column(ForeignKey("guidance_items.id", ondelete="SET NULL"), nullable=True, index=True, comment="匹配指导书条目ID")
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="证据类型")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="证据标题")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="证据摘要")
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="证据正文或抽取文本")
    ocr_result_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="OCR结构化结果JSON")
    ocr_status: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="OCR状态")
    ocr_provider: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="OCR提供方")
    ocr_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="OCR处理时间")
    device: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="关联设备名称")
    ports_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="端口或网络信息JSON")
    evidence_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True, comment="证据时间")
    tags_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="证据标签JSON")
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="来源引用标识")
    asset_match_score: Mapped[float | None] = mapped_column(Float, nullable=True, comment="测试对象匹配得分")
    asset_match_reasons_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="测试对象匹配原因JSON")
    asset_match_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True, comment="测试对象匹配状态")
    guidance_match_score: Mapped[float | None] = mapped_column(Float, nullable=True, comment="指导书匹配得分")
    guidance_match_reasons_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="指导书匹配原因JSON")
    guidance_match_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True, comment="指导书匹配状态")

    project = relationship("Project", back_populates="evidences")
    asset = relationship("Asset", back_populates="evidences", foreign_keys=[asset_id])
    matched_asset = relationship("Asset", back_populates="matched_evidences", foreign_keys=[matched_asset_id])
    matched_guidance = relationship("GuidanceItem", back_populates="matched_evidences", foreign_keys=[matched_guidance_id])
    extracted_fields = relationship("ExtractedField", back_populates="evidence")
    evaluation_record_links = relationship("EvaluationRecordEvidence", back_populates="evidence", cascade="all, delete-orphan")
