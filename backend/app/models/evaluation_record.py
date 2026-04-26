from datetime import datetime, UTC

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, PrimaryKeyConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EvaluationRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evaluation_records"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属项目ID")
    template_id: Mapped[str | None] = mapped_column(ForeignKey("templates.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联模板ID")
    evaluation_item_id: Mapped[str | None] = mapped_column(ForeignKey("evaluation_items.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联测评项ID")
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联文件资产ID")
    title: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True, comment="记录标题")
    template_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="模板编码")
    item_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="测评条目编码")
    matched_fields_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="命中字段快照JSON")
    match_candidates_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="候选匹配结果JSON")
    match_reasons_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="匹配原因JSON")
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True, comment="匹配得分")
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True, comment="复核意见")
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="复核人")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="复核时间")
    final_content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="最终确认内容")
    record_no: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="记录编号")
    sheet_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True, comment="来源工作表名称")
    indicator_l1: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="一级指标")
    indicator_l2: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True, comment="二级指标")
    indicator_l3: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="三级指标")
    record_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="测评记录内容")
    conclusion: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="结论")
    risk_level: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="风险等级")
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True, comment="整改建议")
    template_snapshot_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="模板行快照JSON")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", comment="记录状态")
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual", index=True, comment="来源类型")
    source_row_no: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="来源行号")

    project = relationship("Project", back_populates="evaluation_records")
    template = relationship("Template", back_populates="evaluation_records")
    evaluation_item = relationship("EvaluationItem", back_populates="evaluation_records")
    asset = relationship("Asset", back_populates="evaluation_records")
    extracted_fields = relationship("ExtractedField", back_populates="evaluation_record")
    evidence_links = relationship("EvaluationRecordEvidence", back_populates="evaluation_record", cascade="all, delete-orphan")


class EvaluationRecordEvidence(Base):
    __tablename__ = "evaluation_record_evidences"
    __table_args__ = (
        PrimaryKeyConstraint("evaluation_record_id", "evidence_id", name="pk_evaluation_record_evidences"),
    )

    evaluation_record_id: Mapped[str] = mapped_column(ForeignKey("evaluation_records.id", ondelete="CASCADE"), comment="测评记录ID")
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidences.id", ondelete="CASCADE"), comment="证据ID")
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False, default="supports", comment="关联类型")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        comment="创建时间",
    )

    evaluation_record = relationship("EvaluationRecord", back_populates="evidence_links")
    evidence = relationship("Evidence", back_populates="evaluation_record_links")
