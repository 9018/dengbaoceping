"""add export mode column

Revision ID: 0013_add_export_mode
Revises: 0012_drop_asset_file_sha256_unique
Create Date: 2026-04-26 01:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0013_add_export_mode"
down_revision: Union[str, None] = "0012_drop_asset_file_sha256_unique"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("export_jobs", sa.Column("mode", sa.String(length=20), nullable=True, comment="导出模式"))


def downgrade() -> None:
    op.drop_column("export_jobs", "mode")
