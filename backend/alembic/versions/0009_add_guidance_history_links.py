"""add guidance history links

Revision ID: 0009_add_guidance_history_links
Revises: 0008_add_history_records
Create Date: 2026-04-25 13:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_add_guidance_history_links"
down_revision: Union[str, None] = "0008_add_history_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guidance_history_links",
        sa.Column("guidance_item_id", sa.String(length=36), nullable=False, comment="指导书条目ID"),
        sa.Column("history_record_id", sa.String(length=36), nullable=False, comment="历史记录ID"),
        sa.Column("match_score", sa.Float(), nullable=False, comment="匹配得分"),
        sa.Column("match_reason", sa.JSON(), nullable=False, server_default="{}", comment="匹配原因"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.ForeignKeyConstraint(["guidance_item_id"], ["guidance_items.id"], name=op.f("fk_guidance_history_links_guidance_item_id_guidance_items"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["history_record_id"], ["history_records.id"], name=op.f("fk_guidance_history_links_history_record_id_history_records"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_guidance_history_links")),
        sa.UniqueConstraint("guidance_item_id", "history_record_id", name="uq_guidance_history_links_guidance_item_id_history_record_id"),
    )
    op.create_index(op.f("ix_guidance_history_links_guidance_item_id"), "guidance_history_links", ["guidance_item_id"], unique=False)
    op.create_index(op.f("ix_guidance_history_links_history_record_id"), "guidance_history_links", ["history_record_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_guidance_history_links_history_record_id"), table_name="guidance_history_links")
    op.drop_index(op.f("ix_guidance_history_links_guidance_item_id"), table_name="guidance_history_links")
    op.drop_table("guidance_history_links")
