"""add ocr and extracted field columns

Revision ID: 0002_add_ocr_and_extracted_fields
Revises: 0001_initial_schema
Create Date: 2026-04-24 01:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_ocr_and_extracted_fields"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evidences", sa.Column("ocr_result_json", sa.JSON(), nullable=True, comment="OCR结构化结果JSON"))
    op.add_column("evidences", sa.Column("ocr_status", sa.String(length=50), nullable=True, comment="OCR状态"))
    op.add_column("evidences", sa.Column("ocr_provider", sa.String(length=50), nullable=True, comment="OCR提供方"))
    op.add_column("evidences", sa.Column("ocr_processed_at", sa.DateTime(timezone=True), nullable=True, comment="OCR处理时间"))

    op.add_column("extracted_fields", sa.Column("raw_value", sa.Text(), nullable=True, comment="原始抽取值"))
    op.add_column("extracted_fields", sa.Column("corrected_value", sa.Text(), nullable=True, comment="纠正后值"))
    op.add_column("extracted_fields", sa.Column("source_text", sa.Text(), nullable=True, comment="来源文本片段"))
    op.add_column("extracted_fields", sa.Column("status", sa.String(length=50), nullable=True, comment="抽取状态"))
    op.add_column("extracted_fields", sa.Column("rule_id", sa.String(length=100), nullable=True, comment="命中规则ID"))


def downgrade() -> None:
    op.drop_column("extracted_fields", "rule_id")
    op.drop_column("extracted_fields", "status")
    op.drop_column("extracted_fields", "source_text")
    op.drop_column("extracted_fields", "corrected_value")
    op.drop_column("extracted_fields", "raw_value")

    op.drop_column("evidences", "ocr_processed_at")
    op.drop_column("evidences", "ocr_provider")
    op.drop_column("evidences", "ocr_status")
    op.drop_column("evidences", "ocr_result_json")
