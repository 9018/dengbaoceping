from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExportJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "export_jobs"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属项目ID")
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="txt", comment="导出格式")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed", comment="导出任务状态")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="导出文件名")
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False, comment="导出文件绝对路径")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="导出文件大小")
    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="导出记录数")

    project = relationship("Project", back_populates="export_jobs")
