from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeImportBatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "knowledge_import_batches"

    library_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="知识库类型")
    source_file: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="来源文件")
    source_file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True, comment="来源文件哈希")
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="文件大小")
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="导入条目数量")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True, comment="导入状态")
    duplicate_of_id: Mapped[str | None] = mapped_column(ForeignKey("knowledge_import_batches.id", ondelete="SET NULL"), nullable=True, index=True, comment="重复批次ID")
    import_mode: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="导入模式")
    summary_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment="导入摘要JSON")

    duplicate_of = relationship("KnowledgeImportBatch", remote_side="KnowledgeImportBatch.id")
