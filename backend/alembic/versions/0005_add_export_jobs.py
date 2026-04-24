"""add export jobs table

Revision ID: 0005_add_export_jobs
Revises: 0004_add_manual_review_fields
Create Date: 2026-04-24 16:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_add_export_jobs"
down_revision: Union[str, None] = "0004_add_manual_review_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "export_jobs",
        sa.Column("project_id", sa.String(length=36), nullable=False, comment="所属项目ID"),
        sa.Column("format", sa.String(length=20), nullable=False, comment="导出格式"),
        sa.Column("status", sa.String(length=50), nullable=False, comment="导出任务状态"),
        sa.Column("file_name", sa.String(length=255), nullable=False, comment="导出文件名"),
        sa.Column("file_path", sa.String(length=1000), nullable=False, comment="导出文件绝对路径"),
        sa.Column("file_size", sa.Integer(), nullable=False, comment="导出文件大小"),
        sa.Column("record_count", sa.Integer(), nullable=False, comment="导出记录数"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_export_jobs_project_id_projects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_export_jobs")),
    )
    op.create_index(op.f("ix_export_jobs_project_id"), "export_jobs", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_export_jobs_project_id"), table_name="export_jobs")
    op.drop_table("export_jobs")
