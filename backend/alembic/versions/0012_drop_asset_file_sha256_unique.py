"""drop unique constraint on asset file sha256

Revision ID: 0012_drop_asset_file_sha256_unique
Revises: 0011_add_evidence_guidance_matching
Create Date: 2026-04-26 00:47:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0012_drop_asset_file_sha256_unique"
down_revision: Union[str, None] = "0011_add_evidence_guidance_matching"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        with op.batch_alter_table("assets") as batch_op:
            batch_op.drop_constraint("uq_assets_file_sha256", type_="unique")
    else:
        op.drop_constraint("uq_assets_file_sha256", "assets", type_="unique")


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        with op.batch_alter_table("assets") as batch_op:
            batch_op.create_unique_constraint("uq_assets_file_sha256", ["file_sha256"])
    else:
        op.create_unique_constraint("uq_assets_file_sha256", "assets", ["file_sha256"])
