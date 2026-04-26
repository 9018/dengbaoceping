from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Asset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assets"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属项目ID")
    asset_kind: Mapped[str] = mapped_column(String(50), nullable=False, default="test_object", index=True, comment="资产用途类型")
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="文件分类标识")
    category_label: Mapped[str] = mapped_column(String(100), nullable=False, comment="文件分类中文名称")
    batch_no: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True, comment="上传批次号")
    filename: Mapped[str] = mapped_column(String(255), nullable=False, comment="文件名称")
    primary_ip: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="主IP地址")
    file_ext: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="文件扩展名")
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="文件MIME类型")
    relative_path: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, comment="相对存储路径")
    absolute_path: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="绝对存储路径")
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="文件大小字节数")
    file_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="文件SHA256摘要")
    file_mtime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="文件最后修改时间")
    source: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="文件来源")
    ingest_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", comment="入库处理状态")

    project = relationship("Project", back_populates="assets")
    evidences = relationship("Evidence", back_populates="asset", foreign_keys="Evidence.asset_id")
    matched_evidences = relationship("Evidence", back_populates="matched_asset", foreign_keys="Evidence.matched_asset_id")
    extracted_fields = relationship("ExtractedField", back_populates="asset")
    evidence_facts = relationship("EvidenceFact", back_populates="asset")
    source_templates = relationship("Template", back_populates="source_asset")
    evaluation_records = relationship("EvaluationRecord", back_populates="asset")
    project_assessment_tables = relationship("ProjectAssessmentTable", back_populates="asset", cascade="all, delete-orphan")
    project_assessment_items = relationship("ProjectAssessmentItem", back_populates="asset", cascade="all, delete-orphan")
