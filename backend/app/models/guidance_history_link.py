from sqlalchemy import JSON, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GuidanceHistoryLink(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "guidance_history_links"
    __table_args__ = (
        UniqueConstraint("guidance_item_id", "history_record_id", name="uq_guidance_history_links_guidance_item_id_history_record_id"),
    )

    guidance_item_id: Mapped[str] = mapped_column(ForeignKey("guidance_items.id", ondelete="CASCADE"), nullable=False, index=True, comment="指导书条目ID")
    history_record_id: Mapped[str] = mapped_column(ForeignKey("history_records.id", ondelete="CASCADE"), nullable=False, index=True, comment="历史记录ID")
    match_score: Mapped[float] = mapped_column(Float, nullable=False, comment="匹配得分")
    match_reason: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, comment="匹配原因")
