from sqlalchemy import JSON, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class HistoryRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "history_records"

    source_file: Mapped[str] = mapped_column(String(255), nullable=False, comment="来源文件")
    sheet_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="工作表名称")
    asset_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="资产名称")
    asset_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="资产类型")
    extension_standard: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="扩展标准")
    control_point: Mapped[str | None] = mapped_column(String(1000), nullable=True, index=True, comment="控制点")
    evaluation_item: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="测评项")
    record_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="结果记录")
    compliance_status: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="符合情况")
    score: Mapped[float | None] = mapped_column(Float, nullable=True, comment="分值")
    item_no: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="编号")
    row_index: Mapped[int] = mapped_column(Integer, nullable=False, comment="行号")
    keywords_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, comment="关键词列表")
