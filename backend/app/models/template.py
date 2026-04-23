from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Template(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "templates"

    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True, comment="所属项目ID")
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="模板名称")
    template_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="模板类型")
    extension_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True, comment="扩展类型")
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="领域名称")
    level2: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="关联二级指标")
    version: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="模板版本")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="模板说明")
    source_asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True, comment="来源文件资产ID")
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否系统内置")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")

    project = relationship("Project", back_populates="templates")
    source_asset = relationship("Asset", back_populates="source_templates")
    evaluation_items = relationship("EvaluationItem", back_populates="template", cascade="all, delete-orphan")
    evaluation_records = relationship("EvaluationRecord", back_populates="template")
    extracted_fields = relationship("ExtractedField", back_populates="template")
