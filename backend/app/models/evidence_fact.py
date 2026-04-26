from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EvidenceFact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evidence_facts"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属项目ID")
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属资产ID")
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidences.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属证据ID")
    project_assessment_item_id: Mapped[str | None] = mapped_column(
        ForeignKey("project_assessment_items.id", ondelete="SET NULL"), nullable=True, index=True, comment="匹配项目测评项ID"
    )
    matched_template_item_id: Mapped[str | None] = mapped_column(
        ForeignKey("assessment_template_items.id", ondelete="SET NULL"), nullable=True, index=True, comment="匹配主模板项ID"
    )
    page_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="页面类型")
    fact_group: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="事实分组")
    fact_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="事实键")
    fact_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="事实名称")
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True, comment="原始事实值")
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True, comment="归一化事实值")
    value_number: Mapped[float | None] = mapped_column(Float, nullable=True, comment="数值类型事实值")
    value_bool: Mapped[bool | None] = mapped_column(Boolean, nullable=True, comment="布尔类型事实值")
    value_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="JSON类型事实值")
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="来源文本")
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="来源页码")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True, comment="识别置信度")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="identified", index=True, comment="事实状态")

    project = relationship("Project", back_populates="evidence_facts")
    asset = relationship("Asset", back_populates="evidence_facts")
    evidence = relationship("Evidence", back_populates="evidence_facts")
    project_assessment_item = relationship("ProjectAssessmentItem", back_populates="evidence_facts")
    matched_template_item = relationship("AssessmentTemplateItem", back_populates="evidence_facts")
