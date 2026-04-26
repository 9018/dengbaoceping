"""add project template workbook fields

Revision ID: 0015_add_project_template_workbook_fields
Revises: 0014_add_historical_assessment_fields
Create Date: 2026-04-26 18:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0015_add_project_template_workbook_fields"
down_revision: Union[str, None] = "0014_add_historical_assessment_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evaluation_items", sa.Column("control_point", sa.String(length=500), nullable=True, comment="控制点"))
    op.add_column("evaluation_items", sa.Column("extension_standard", sa.String(length=255), nullable=True, comment="扩展标准"))
    op.add_column("evaluation_items", sa.Column("record_template", sa.Text(), nullable=True, comment="结果记录模板"))
    op.add_column("evaluation_items", sa.Column("default_compliance", sa.String(length=100), nullable=True, comment="默认符合情况"))
    op.add_column("evaluation_items", sa.Column("score_weight", sa.Float(), nullable=True, comment="权重/分值"))
    op.add_column("evaluation_items", sa.Column("item_no", sa.String(length=100), nullable=True, comment="编号"))
    op.add_column("evaluation_items", sa.Column("source_row_no", sa.Integer(), nullable=True, comment="来源行号"))
    op.add_column("evaluation_items", sa.Column("keywords_json", sa.JSON(), nullable=True, comment="关键词快照JSON"))
    op.create_index(op.f("ix_evaluation_items_item_no"), "evaluation_items", ["item_no"], unique=False)

    op.add_column("evaluation_records", sa.Column("template_snapshot_json", sa.JSON(), nullable=True, comment="模板行快照JSON"))


def downgrade() -> None:
    op.drop_column("evaluation_records", "template_snapshot_json")

    op.drop_index(op.f("ix_evaluation_items_item_no"), table_name="evaluation_items")
    op.drop_column("evaluation_items", "keywords_json")
    op.drop_column("evaluation_items", "source_row_no")
    op.drop_column("evaluation_items", "item_no")
    op.drop_column("evaluation_items", "score_weight")
    op.drop_column("evaluation_items", "default_compliance")
    op.drop_column("evaluation_items", "record_template")
    op.drop_column("evaluation_items", "extension_standard")
    op.drop_column("evaluation_items", "control_point")
