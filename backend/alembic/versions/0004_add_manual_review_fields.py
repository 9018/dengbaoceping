"""add manual review fields and audit logs

Revision ID: 0004_add_manual_review_fields
Revises: 0003_add_record_generation_fields
Create Date: 2026-04-24 04:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_add_manual_review_fields"
down_revision: Union[str, None] = "0003_add_record_generation_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("extracted_fields", sa.Column("review_comment", sa.Text(), nullable=True, comment="复核意见"))
    op.add_column("extracted_fields", sa.Column("reviewed_by", sa.String(length=100), nullable=True, comment="复核人"))
    op.add_column("extracted_fields", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True, comment="复核时间"))

    op.add_column("evaluation_records", sa.Column("reviewed_by", sa.String(length=100), nullable=True, comment="复核人"))
    op.add_column("evaluation_records", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True, comment="复核时间"))
    op.add_column("evaluation_records", sa.Column("final_content", sa.Text(), nullable=True, comment="最终确认内容"))

    op.create_table(
        "review_audit_logs",
        sa.Column("target_type", sa.String(length=50), nullable=False, comment="审计对象类型"),
        sa.Column("target_id", sa.String(length=36), nullable=False, comment="审计对象ID"),
        sa.Column("action", sa.String(length=50), nullable=False, comment="操作动作"),
        sa.Column("changed_fields_json", sa.JSON(), nullable=True, comment="变更字段JSON"),
        sa.Column("review_comment", sa.Text(), nullable=True, comment="复核意见"),
        sa.Column("reviewed_by", sa.String(length=100), nullable=True, comment="操作人"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_audit_logs")),
    )
    op.create_index(op.f("ix_review_audit_logs_target_type"), "review_audit_logs", ["target_type"], unique=False)
    op.create_index(op.f("ix_review_audit_logs_target_id"), "review_audit_logs", ["target_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_review_audit_logs_target_id"), table_name="review_audit_logs")
    op.drop_index(op.f("ix_review_audit_logs_target_type"), table_name="review_audit_logs")
    op.drop_table("review_audit_logs")

    op.drop_column("evaluation_records", "final_content")
    op.drop_column("evaluation_records", "reviewed_at")
    op.drop_column("evaluation_records", "reviewed_by")

    op.drop_column("extracted_fields", "reviewed_at")
    op.drop_column("extracted_fields", "reviewed_by")
    op.drop_column("extracted_fields", "review_comment")
