"""add evidence guidance matching

Revision ID: 0011_add_evidence_guidance_matching
Revises: 0010_add_evidence_asset_matching
Create Date: 2026-04-25 19:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


FK_NAME = "fk_evidences_matched_guidance_id_guidance_items"

revision: str = "0011_add_evidence_guidance_matching"
down_revision: Union[str, None] = "0010_add_evidence_asset_matching"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.add_column("evidences", sa.Column("matched_guidance_id", sa.String(length=36), nullable=True, comment="匹配指导书条目ID"))
    op.add_column("evidences", sa.Column("guidance_match_score", sa.Float(), nullable=True, comment="指导书匹配得分"))
    op.add_column("evidences", sa.Column("guidance_match_reasons_json", sa.JSON(), nullable=True, comment="指导书匹配原因JSON"))
    op.add_column("evidences", sa.Column("guidance_match_status", sa.String(length=50), nullable=True, server_default="pending", comment="指导书匹配状态"))
    if dialect != "sqlite":
        op.create_foreign_key(
            FK_NAME,
            "evidences",
            "guidance_items",
            ["matched_guidance_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(op.f("ix_evidences_matched_guidance_id"), "evidences", ["matched_guidance_id"], unique=False)
    op.create_index(op.f("ix_evidences_guidance_match_status"), "evidences", ["guidance_match_status"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.drop_index(op.f("ix_evidences_guidance_match_status"), table_name="evidences")
    op.drop_index(op.f("ix_evidences_matched_guidance_id"), table_name="evidences")
    if dialect != "sqlite":
        op.drop_constraint(FK_NAME, "evidences", type_="foreignkey")
    op.drop_column("evidences", "guidance_match_status")
    op.drop_column("evidences", "guidance_match_reasons_json")
    op.drop_column("evidences", "guidance_match_score")
    op.drop_column("evidences", "matched_guidance_id")
