"""add match candidates to evaluation records

Revision ID: 0006_add_match_candidates_to_records
Revises: 0005_add_export_jobs
Create Date: 2026-04-25 00:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_add_match_candidates_to_records"
down_revision: Union[str, None] = "0005_add_export_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evaluation_records", sa.Column("match_candidates_json", sa.JSON(), nullable=True, comment="候选匹配结果JSON"))


def downgrade() -> None:
    op.drop_column("evaluation_records", "match_candidates_json")
