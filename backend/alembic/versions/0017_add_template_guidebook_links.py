"""add template guidebook links

Revision ID: 0017_add_template_guidebook_links
Revises: 0016_add_assessment_template_library
Create Date: 2026-04-26 22:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0017_add_template_guidebook_links"
down_revision: Union[str, None] = "0016_add_assessment_template_library"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "template_guidebook_links",
        sa.Column("template_item_id", sa.String(length=36), nullable=False, comment="模板项ID"),
        sa.Column("guidance_item_id", sa.String(length=36), nullable=False, comment="指导书条目ID"),
        sa.Column("match_score", sa.Float(), nullable=False, comment="匹配得分"),
        sa.Column("match_reason", sa.JSON(), nullable=False, server_default=sa.text("'{}'"), comment="匹配原因"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.ForeignKeyConstraint(["guidance_item_id"], ["guidance_items.id"], name=op.f("fk_template_guidebook_links_guidance_item_id_guidance_items"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_item_id"], ["assessment_template_items.id"], name=op.f("fk_template_guidebook_links_template_item_id_assessment_template_items"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_template_guidebook_links")),
        sa.UniqueConstraint("template_item_id", "guidance_item_id", name="uq_template_guidebook_links_template_item_id_guidance_item_id"),
    )
    op.create_index(op.f("ix_template_guidebook_links_guidance_item_id"), "template_guidebook_links", ["guidance_item_id"], unique=False)
    op.create_index(op.f("ix_template_guidebook_links_template_item_id"), "template_guidebook_links", ["template_item_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_template_guidebook_links_template_item_id"), table_name="template_guidebook_links")
    op.drop_index(op.f("ix_template_guidebook_links_guidance_item_id"), table_name="template_guidebook_links")
    op.drop_table("template_guidebook_links")
