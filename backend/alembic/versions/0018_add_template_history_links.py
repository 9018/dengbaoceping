"""add template history links

Revision ID: 0018_add_template_history_links
Revises: 0017_add_template_guidebook_links
Create Date: 2026-04-26 23:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0018_add_template_history_links"
down_revision: Union[str, None] = "0017_add_template_guidebook_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "template_history_links",
        sa.Column("template_item_id", sa.String(length=36), nullable=False, comment="模板项ID"),
        sa.Column("history_record_id", sa.String(length=36), nullable=False, comment="历史记录ID"),
        sa.Column("match_score", sa.Float(), nullable=False, comment="匹配得分"),
        sa.Column("match_reason", sa.JSON(), nullable=False, server_default=sa.text("'{}'"), comment="匹配原因"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.ForeignKeyConstraint(["history_record_id"], ["history_records.id"], name=op.f("fk_template_history_links_history_record_id_history_records"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_item_id"], ["assessment_template_items.id"], name=op.f("fk_template_history_links_template_item_id_assessment_template_items"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_template_history_links")),
        sa.UniqueConstraint("template_item_id", "history_record_id", name="uq_template_history_links_template_item_id_history_record_id"),
    )
    op.create_index(op.f("ix_template_history_links_history_record_id"), "template_history_links", ["history_record_id"], unique=False)
    op.create_index(op.f("ix_template_history_links_template_item_id"), "template_history_links", ["template_item_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_template_history_links_template_item_id"), table_name="template_history_links")
    op.drop_index(op.f("ix_template_history_links_history_record_id"), table_name="template_history_links")
    op.drop_table("template_history_links")
