"""add evidence asset matching

Revision ID: 0010_add_evidence_asset_matching
Revises: 0009_add_guidance_history_links
Create Date: 2026-04-25 16:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_add_evidence_asset_matching"
down_revision: Union[str, None] = "0009_add_guidance_history_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FK_NAME = "fk_evidences_matched_asset_id_assets"


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.add_column("assets", sa.Column("asset_kind", sa.String(length=50), nullable=True, server_default="test_object", comment="资产用途类型"))
    op.add_column("assets", sa.Column("primary_ip", sa.String(length=100), nullable=True, comment="主IP地址"))
    op.create_index(op.f("ix_assets_asset_kind"), "assets", ["asset_kind"], unique=False)
    op.create_index(op.f("ix_assets_primary_ip"), "assets", ["primary_ip"], unique=False)

    op.execute(
        """
        UPDATE assets
        SET asset_kind = CASE
            WHEN source = 'upload' OR category = 'evidence' THEN 'evidence_file'
            ELSE 'test_object'
        END
        """
    )
    if dialect != "sqlite":
        op.alter_column("assets", "asset_kind", existing_type=sa.String(length=50), nullable=False, server_default="test_object")

    op.add_column("evidences", sa.Column("matched_asset_id", sa.String(length=36), nullable=True, comment="匹配测试对象资产ID"))
    op.add_column("evidences", sa.Column("asset_match_score", sa.Float(), nullable=True, comment="测试对象匹配得分"))
    op.add_column("evidences", sa.Column("asset_match_reasons_json", sa.JSON(), nullable=True, comment="测试对象匹配原因JSON"))
    op.add_column("evidences", sa.Column("asset_match_status", sa.String(length=50), nullable=True, server_default="pending", comment="测试对象匹配状态"))
    if dialect != "sqlite":
        op.create_foreign_key(
            FK_NAME,
            "evidences",
            "assets",
            ["matched_asset_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(op.f("ix_evidences_matched_asset_id"), "evidences", ["matched_asset_id"], unique=False)
    op.create_index(op.f("ix_evidences_asset_match_status"), "evidences", ["asset_match_status"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.drop_index(op.f("ix_evidences_asset_match_status"), table_name="evidences")
    op.drop_index(op.f("ix_evidences_matched_asset_id"), table_name="evidences")
    if dialect != "sqlite":
        op.drop_constraint(FK_NAME, "evidences", type_="foreignkey")
    op.drop_column("evidences", "asset_match_status")
    op.drop_column("evidences", "asset_match_reasons_json")
    op.drop_column("evidences", "asset_match_score")
    op.drop_column("evidences", "matched_asset_id")

    op.drop_index(op.f("ix_assets_primary_ip"), table_name="assets")
    op.drop_index(op.f("ix_assets_asset_kind"), table_name="assets")
    op.drop_column("assets", "primary_ip")
    op.drop_column("assets", "asset_kind")
