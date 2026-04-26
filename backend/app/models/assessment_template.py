from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AssessmentTemplateWorkbook(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assessment_template_workbooks"

    source_file: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="来源文件")
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="模板名称")
    version: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="模板版本")
    sheet_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="工作表数量")
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="模板项数量")

    sheets = relationship("AssessmentTemplateSheet", back_populates="workbook", cascade="all, delete-orphan")
    items = relationship("AssessmentTemplateItem", back_populates="workbook", cascade="all, delete-orphan")


class AssessmentTemplateSheet(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assessment_template_sheets"

    workbook_id: Mapped[str] = mapped_column(ForeignKey("assessment_template_workbooks.id", ondelete="CASCADE"), nullable=False, index=True, comment="模板工作簿ID")
    sheet_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="工作表名称")
    object_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="对象类型")
    object_category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="对象分类")
    object_subtype: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="对象子类型")
    is_physical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否物理环境")
    is_network: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否网络对象")
    is_security_device: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否安全设备")
    is_server: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否服务器")
    is_database: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否数据库")
    is_middleware: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否中间件")
    is_application: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否应用系统")
    is_data_object: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否数据对象")
    is_management: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否管理对象")
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="解析行数")

    workbook = relationship("AssessmentTemplateWorkbook", back_populates="sheets")
    items = relationship("AssessmentTemplateItem", back_populates="sheet", cascade="all, delete-orphan")


class AssessmentTemplateItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assessment_template_items"

    workbook_id: Mapped[str] = mapped_column(ForeignKey("assessment_template_workbooks.id", ondelete="CASCADE"), nullable=False, index=True, comment="模板工作簿ID")
    sheet_id: Mapped[str] = mapped_column(ForeignKey("assessment_template_sheets.id", ondelete="CASCADE"), nullable=False, index=True, comment="模板工作表ID")
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
    raw_row_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="原始行JSON")

    workbook = relationship("AssessmentTemplateWorkbook", back_populates="items")
    sheet = relationship("AssessmentTemplateSheet", back_populates="items")
    guidebook_links = relationship("TemplateGuidebookLink", back_populates="template_item", cascade="all, delete-orphan")
    history_links = relationship("TemplateHistoryLink", back_populates="template_item", cascade="all, delete-orphan")
    project_assessment_items = relationship("ProjectAssessmentItem", back_populates="source_template_item")
    evidence_facts = relationship("EvidenceFact", back_populates="matched_template_item")


class TemplateGuidebookLink(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "template_guidebook_links"
    __table_args__ = (
        UniqueConstraint("template_item_id", "guidance_item_id", name="uq_template_guidebook_links_template_item_id_guidance_item_id"),
    )

    template_item_id: Mapped[str] = mapped_column(ForeignKey("assessment_template_items.id", ondelete="CASCADE"), nullable=False, index=True, comment="模板项ID")
    guidance_item_id: Mapped[str] = mapped_column(ForeignKey("guidance_items.id", ondelete="CASCADE"), nullable=False, index=True, comment="指导书条目ID")
    match_score: Mapped[float] = mapped_column(Float, nullable=False, comment="匹配得分")
    match_reason: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, comment="匹配原因")

    template_item = relationship("AssessmentTemplateItem", back_populates="guidebook_links")
    guidance_item = relationship("GuidanceItem")


class TemplateHistoryLink(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "template_history_links"
    __table_args__ = (
        UniqueConstraint("template_item_id", "history_record_id", name="uq_template_history_links_template_item_id_history_record_id"),
    )

    template_item_id: Mapped[str] = mapped_column(ForeignKey("assessment_template_items.id", ondelete="CASCADE"), nullable=False, index=True, comment="模板项ID")
    history_record_id: Mapped[str] = mapped_column(ForeignKey("history_records.id", ondelete="CASCADE"), nullable=False, index=True, comment="历史记录ID")
    match_score: Mapped[float] = mapped_column(Float, nullable=False, comment="匹配得分")
    match_reason: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, comment="匹配原因")

    template_item = relationship("AssessmentTemplateItem", back_populates="history_links")
    history_record = relationship("HistoricalAssessmentRecord")
