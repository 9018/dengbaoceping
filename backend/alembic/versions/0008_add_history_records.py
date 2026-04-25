"""add history records

Revision ID: 0008_add_history_records
Revises: 0007_add_guidance_items
Create Date: 2026-04-25 11:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_add_history_records"
down_revision: Union[str, None] = "0007_add_guidance_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "history_records",
        sa.Column("source_file", sa.String(length=255), nullable=False, comment="来源文件"),
        sa.Column("sheet_name", sa.String(length=255), nullable=False, comment="工作表名称"),
        sa.Column("asset_name", sa.String(length=255), nullable=False, comment="资产名称"),
        sa.Column("asset_type", sa.String(length=100), nullable=True, comment="资产类型"),
        sa.Column("extension_standard", sa.String(length=255), nullable=True, comment="扩展标准"),
        sa.Column("control_point", sa.String(length=1000), nullable=True, comment="控制点"),
        sa.Column("evaluation_item", sa.String(length=1000), nullable=True, comment="测评项"),
        sa.Column("record_text", sa.Text(), nullable=True, comment="结果记录"),
        sa.Column("compliance_status", sa.String(length=100), nullable=True, comment="符合情况"),
        sa.Column("score", sa.Float(), nullable=True, comment="分值"),
        sa.Column("item_no", sa.String(length=100), nullable=True, comment="编号"),
        sa.Column("row_index", sa.Integer(), nullable=False, comment="行号"),
        sa.Column("keywords_json", sa.JSON(), nullable=False, server_default="[]", comment="关键词列表"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_history_records")),
    )
    op.create_index(op.f("ix_history_records_sheet_name"), "history_records", ["sheet_name"], unique=False)
    op.create_index(op.f("ix_history_records_asset_name"), "history_records", ["asset_name"], unique=False)
    op.create_index(op.f("ix_history_records_asset_type"), "history_records", ["asset_type"], unique=False)
    op.create_index(op.f("ix_history_records_control_point"), "history_records", ["control_point"], unique=False)
    op.create_index(op.f("ix_history_records_compliance_status"), "history_records", ["compliance_status"], unique=False)
    op.create_index(op.f("ix_history_records_item_no"), "history_records", ["item_no"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_history_records_item_no"), table_name="history_records")
    op.drop_index(op.f("ix_history_records_compliance_status"), table_name="history_records")
    op.drop_index(op.f("ix_history_records_control_point"), table_name="history_records")
    op.drop_index(op.f("ix_history_records_asset_type"), table_name="history_records")
    op.drop_index(op.f("ix_history_records_asset_name"), table_name="history_records")
    op.drop_index(op.f("ix_history_records_sheet_name"), table_name="history_records")
    op.drop_table("history_records")
