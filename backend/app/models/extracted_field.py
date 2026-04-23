from datetime import datetime, UTC

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExtractedField(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "extracted_fields"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属项目ID")
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联文件资产ID")
    evidence_id: Mapped[str | None] = mapped_column(ForeignKey("evidences.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联证据ID")
    template_id: Mapped[str | None] = mapped_column(ForeignKey("templates.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联模板ID")
    record_id: Mapped[str | None] = mapped_column(ForeignKey("evaluation_records.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联测评记录ID")
    field_group: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="字段分组")
    field_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="字段名称")
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True, comment="原始抽取值")
    corrected_value: Mapped[str | None] = mapped_column(Text, nullable=True, comment="纠正后值")
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="来源文本片段")
    status: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="抽取状态")
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True, comment="复核意见")
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="复核人")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="复核时间")
    rule_id: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="命中规则ID")
    field_value_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="文本类型字段值")
    field_value_number: Mapped[float | None] = mapped_column(Float, nullable=True, comment="数值类型字段值")
    field_value_bool: Mapped[bool | None] = mapped_column(Boolean, nullable=True, comment="布尔类型字段值")
    field_value_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="JSON类型字段值")
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="来源页码")
    source_sheet: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="来源工作表")
    source_row: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="来源行号")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True, comment="抽取置信度")

    project = relationship("Project", back_populates="extracted_fields")
    asset = relationship("Asset", back_populates="extracted_fields")
    evidence = relationship("Evidence", back_populates="extracted_fields")
    template = relationship("Template", back_populates="extracted_fields")
    evaluation_record = relationship("EvaluationRecord", back_populates="extracted_fields")


class ReviewAuditLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "review_audit_logs"

    target_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="审计对象类型")
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="审计对象ID")
    action: Mapped[str] = mapped_column(String(50), nullable=False, comment="操作动作")
    changed_fields_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="变更字段JSON")
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True, comment="复核意见")
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="操作人")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        comment="创建时间",
    )
