from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectAssessmentTable(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project_assessment_tables"
    __table_args__ = (
        UniqueConstraint("project_id", "asset_id", name="uq_project_assessment_tables_project_id_asset_id"),
    )

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属项目ID")
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属资产ID")
    source_workbook_id: Mapped[str | None] = mapped_column(
        ForeignKey("assessment_template_workbooks.id", ondelete="SET NULL"), nullable=True, index=True, comment="来源主模板工作簿ID"
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="项目测评表名称")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True, comment="测评表状态")
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="测评表项数量")

    project = relationship("Project", back_populates="project_assessment_tables")
    asset = relationship("Asset", back_populates="project_assessment_tables")
    source_workbook = relationship("AssessmentTemplateWorkbook")
    items = relationship("ProjectAssessmentItem", back_populates="table", cascade="all, delete-orphan")


class ProjectAssessmentItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project_assessment_items"
    __table_args__ = (
        UniqueConstraint("table_id", "source_template_item_id", name="uq_project_assessment_items_table_id_source_template_item_id"),
    )

    table_id: Mapped[str] = mapped_column(ForeignKey("project_assessment_tables.id", ondelete="CASCADE"), nullable=False, index=True, comment="项目测评表ID")
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属项目ID")
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属资产ID")
    source_template_item_id: Mapped[str | None] = mapped_column(
        ForeignKey("assessment_template_items.id", ondelete="SET NULL"), nullable=True, index=True, comment="来源主模板项ID"
    )
    sheet_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="工作表名称")
    row_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="来源行号")
    standard_type: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="扩展标准")
    control_point: Mapped[str | None] = mapped_column(String(1000), nullable=True, index=True, comment="控制点")
    item_text: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="测评项")
    record_template: Mapped[str | None] = mapped_column(Text, nullable=True, comment="结果记录模板")
    default_compliance_result: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="默认符合情况")
    weight: Mapped[float | None] = mapped_column(Float, nullable=True, comment="权重/分值")
    item_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="编号")
    object_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="对象类型")
    object_category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="对象分类")
    page_types_json: Mapped[list[str] | dict | None] = mapped_column(JSON, nullable=True, comment="页面类型JSON")
    required_facts_json: Mapped[list[str] | dict | None] = mapped_column(JSON, nullable=True, comment="必备事实JSON")
    evidence_keywords_json: Mapped[list[str] | dict | None] = mapped_column(JSON, nullable=True, comment="证据关键词JSON")
    command_keywords_json: Mapped[list[str] | dict | None] = mapped_column(JSON, nullable=True, comment="命令关键词JSON")
    applicability_json: Mapped[list[str] | dict | None] = mapped_column(JSON, nullable=True, comment="适用范围JSON")
    evidence_ids_json: Mapped[list[str] | dict | None] = mapped_column(JSON, nullable=True, comment="关联证据ID JSON")
    evidence_facts_json: Mapped[list[dict] | dict | None] = mapped_column(JSON, nullable=True, comment="证据事实快照JSON")
    guidance_refs_json: Mapped[list[dict] | dict | None] = mapped_column(JSON, nullable=True, comment="指导书引用JSON")
    history_refs_json: Mapped[list[dict] | dict | None] = mapped_column(JSON, nullable=True, comment="历史写法引用JSON")
    draft_record_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="草稿结果记录")
    draft_compliance_result: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="草稿符合情况")
    final_record_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="最终结果记录")
    final_compliance_result: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="最终符合情况")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True, comment="生成置信度")
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True, comment="匹配得分")
    match_reason_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="匹配原因JSON")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True, comment="项目测评项状态")
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True, comment="复核意见")
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="复核人")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="复核时间")

    table = relationship("ProjectAssessmentTable", back_populates="items")
    project = relationship("Project", back_populates="project_assessment_items")
    asset = relationship("Asset", back_populates="project_assessment_items")
    source_template_item = relationship("AssessmentTemplateItem", back_populates="project_assessment_items")
    evidence_facts = relationship("EvidenceFact", back_populates="project_assessment_item")
