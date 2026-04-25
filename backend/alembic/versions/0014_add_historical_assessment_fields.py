"""add historical assessment fields

Revision ID: 0014_add_historical_assessment_fields
Revises: 0013_add_export_mode
Create Date: 2026-04-26 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0014_add_historical_assessment_fields"
down_revision: Union[str, None] = "0013_add_export_mode"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("history_records", sa.Column("project_name", sa.String(length=255), nullable=True, comment="项目名称"))
    op.add_column("history_records", sa.Column("asset_ip", sa.String(length=100), nullable=True, comment="资产IP"))
    op.add_column("history_records", sa.Column("asset_version", sa.String(length=255), nullable=True, comment="资产版本"))
    op.add_column("history_records", sa.Column("standard_type", sa.String(length=255), nullable=True, comment="标准类型"))
    op.add_column("history_records", sa.Column("item_text", sa.String(length=1000), nullable=True, comment="测评项"))
    op.add_column("history_records", sa.Column("raw_text", sa.Text(), nullable=True, comment="原始记录文本"))
    op.add_column("history_records", sa.Column("compliance_result", sa.String(length=100), nullable=True, comment="符合性结果"))
    op.add_column("history_records", sa.Column("score_weight", sa.Float(), nullable=True, comment="权重/分值"))
    op.add_column("history_records", sa.Column("item_code", sa.String(length=100), nullable=True, comment="测评项编号"))
    op.create_index(op.f("ix_history_records_project_name"), "history_records", ["project_name"], unique=False)
    op.create_index(op.f("ix_history_records_asset_ip"), "history_records", ["asset_ip"], unique=False)
    op.create_index(op.f("ix_history_records_compliance_result"), "history_records", ["compliance_result"], unique=False)
    op.create_index(op.f("ix_history_records_item_code"), "history_records", ["item_code"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_history_records_item_code"), table_name="history_records")
    op.drop_index(op.f("ix_history_records_compliance_result"), table_name="history_records")
    op.drop_index(op.f("ix_history_records_asset_ip"), table_name="history_records")
    op.drop_index(op.f("ix_history_records_project_name"), table_name="history_records")
    op.drop_column("history_records", "item_code")
    op.drop_column("history_records", "score_weight")
    op.drop_column("history_records", "compliance_result")
    op.drop_column("history_records", "raw_text")
    op.drop_column("history_records", "item_text")
    op.drop_column("history_records", "standard_type")
    op.drop_column("history_records", "asset_version")
    op.drop_column("history_records", "asset_ip")
    op.drop_column("history_records", "project_name")
