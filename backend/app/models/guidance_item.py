from __future__ import annotations

from sqlalchemy import JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GuidanceItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "guidance_items"
    __table_args__ = (
        UniqueConstraint("guidance_code", name="uq_guidance_items_guidance_code"),
    )

    guidance_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True, comment="指导书章节编码")
    source_file: Mapped[str] = mapped_column(String(255), nullable=False, comment="来源文件路径")
    section_path: Mapped[str] = mapped_column(String(1000), nullable=False, index=True, comment="章节路径")
    section_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="章节标题")
    level1: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True, comment="一级标题")
    level2: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True, comment="二级标题")
    level3: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True, comment="三级标题")
    raw_markdown: Mapped[str] = mapped_column(Text, nullable=False, comment="章节原始Markdown")
    plain_text: Mapped[str] = mapped_column(Text, nullable=False, comment="章节纯文本")
    keywords_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, comment="关键词列表")
    check_points_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, comment="核查要点列表")
    evidence_requirements_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, comment="证据要求列表")
    record_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True, comment="记录建议")
