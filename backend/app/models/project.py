from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "projects"

    code: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, comment="项目编码")
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="项目名称")
    project_type: Mapped[str] = mapped_column(String(100), nullable=False, default="等级保护测评", comment="项目类型")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", comment="项目状态")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="项目说明")
    storage_root: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="项目存储根目录")

    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    evidences = relationship("Evidence", back_populates="project", cascade="all, delete-orphan")
    extracted_fields = relationship("ExtractedField", back_populates="project", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="project", cascade="all, delete-orphan")
    evaluation_records = relationship("EvaluationRecord", back_populates="project", cascade="all, delete-orphan")
    export_jobs = relationship("ExportJob", back_populates="project", cascade="all, delete-orphan")
