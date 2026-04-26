from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EvaluationItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evaluation_items"
    __table_args__ = (
        UniqueConstraint("template_id", "extension_type", "level2", "level3", name="uq_evaluation_items_template_extension_level2_level3"),
    )

    template_id: Mapped[str] = mapped_column(ForeignKey("templates.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属模板ID")
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="归属领域")
    level1: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="一级指标")
    level2: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="二级指标")
    level3: Mapped[str] = mapped_column(String(500), nullable=False, comment="三级指标")
    extension_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="扩展类型")
    route_domain: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="路由领域")
    source_template_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="来源模板名称")
    source_sheet_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="来源工作表名称")
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="排序序号")
    control_point: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="控制点")
    extension_standard: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="扩展标准")
    record_template: Mapped[str | None] = mapped_column(Text, nullable=True, comment="结果记录模板")
    default_compliance: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="默认符合情况")
    score_weight: Mapped[float | None] = mapped_column(Float, nullable=True, comment="权重/分值")
    item_no: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="编号")
    source_row_no: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="来源行号")
    keywords_json: Mapped[list | dict | None] = mapped_column(JSON, nullable=True, comment="关键词快照JSON")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")

    template = relationship("Template", back_populates="evaluation_items")
    evaluation_records = relationship("EvaluationRecord", back_populates="evaluation_item")
