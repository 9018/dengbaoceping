"""add evaluation record generation fields

Revision ID: 0003_add_record_generation_fields
Revises: 0002_add_ocr_and_extracted_fields
Create Date: 2026-04-24 02:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_add_record_generation_fields"
down_revision: Union[str, None] = "0002_add_ocr_and_extracted_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evaluation_records", sa.Column("title", sa.String(length=255), nullable=True, comment="记录标题"))
    op.add_column("evaluation_records", sa.Column("template_code", sa.String(length=100), nullable=True, comment="模板编码"))
    op.add_column("evaluation_records", sa.Column("item_code", sa.String(length=100), nullable=True, comment="测评条目编码"))
    op.add_column("evaluation_records", sa.Column("matched_fields_json", sa.JSON(), nullable=True, comment="命中字段快照JSON"))
    op.add_column("evaluation_records", sa.Column("match_reasons_json", sa.JSON(), nullable=True, comment="匹配原因JSON"))
    op.add_column("evaluation_records", sa.Column("match_score", sa.Float(), nullable=True, comment="匹配得分"))
    op.add_column("evaluation_records", sa.Column("review_comment", sa.Text(), nullable=True, comment="复核意见"))

    op.create_index(op.f("ix_evaluation_records_title"), "evaluation_records", ["title"], unique=False)
    op.create_index(op.f("ix_evaluation_records_template_code"), "evaluation_records", ["template_code"], unique=False)
    op.create_index(op.f("ix_evaluation_records_item_code"), "evaluation_records", ["item_code"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_records_item_code"), table_name="evaluation_records")
    op.drop_index(op.f("ix_evaluation_records_template_code"), table_name="evaluation_records")
    op.drop_index(op.f("ix_evaluation_records_title"), table_name="evaluation_records")

    op.drop_column("evaluation_records", "review_comment")
    op.drop_column("evaluation_records", "match_score")
    op.drop_column("evaluation_records", "match_reasons_json")
    op.drop_column("evaluation_records", "matched_fields_json")
    op.drop_column("evaluation_records", "item_code")
    op.drop_column("evaluation_records", "template_code")
    op.drop_column("evaluation_records", "title")
