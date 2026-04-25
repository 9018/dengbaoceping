"""add guidance items

Revision ID: 0007_add_guidance_items
Revises: 0006_add_match_candidates_to_records
Create Date: 2026-04-25 10:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_add_guidance_items"
down_revision: Union[str, None] = "0006_add_match_candidates_to_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guidance_items",
        sa.Column("guidance_code", sa.String(length=120), nullable=False, comment="指导书章节编码"),
        sa.Column("source_file", sa.String(length=255), nullable=False, comment="来源文件路径"),
        sa.Column("section_path", sa.String(length=1000), nullable=False, comment="章节路径"),
        sa.Column("section_title", sa.String(length=255), nullable=False, comment="章节标题"),
        sa.Column("level1", sa.String(length=255), nullable=True, comment="一级标题"),
        sa.Column("level2", sa.String(length=255), nullable=True, comment="二级标题"),
        sa.Column("level3", sa.String(length=255), nullable=True, comment="三级标题"),
        sa.Column("raw_markdown", sa.Text(), nullable=False, comment="章节原始Markdown"),
        sa.Column("plain_text", sa.Text(), nullable=False, comment="章节纯文本"),
        sa.Column("keywords_json", sa.JSON(), nullable=False, server_default="[]", comment="关键词列表"),
        sa.Column("check_points_json", sa.JSON(), nullable=False, server_default="[]", comment="核查要点列表"),
        sa.Column("evidence_requirements_json", sa.JSON(), nullable=False, server_default="[]", comment="证据要求列表"),
        sa.Column("record_suggestion", sa.Text(), nullable=True, comment="记录建议"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_guidance_items")),
        sa.UniqueConstraint("guidance_code", name="uq_guidance_items_guidance_code"),
    )
    op.create_index(op.f("ix_guidance_items_guidance_code"), "guidance_items", ["guidance_code"], unique=False)
    op.create_index(op.f("ix_guidance_items_level1"), "guidance_items", ["level1"], unique=False)
    op.create_index(op.f("ix_guidance_items_level2"), "guidance_items", ["level2"], unique=False)
    op.create_index(op.f("ix_guidance_items_level3"), "guidance_items", ["level3"], unique=False)
    op.create_index(op.f("ix_guidance_items_section_path"), "guidance_items", ["section_path"], unique=False)
    op.create_index(op.f("ix_guidance_items_section_title"), "guidance_items", ["section_title"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_guidance_items_section_title"), table_name="guidance_items")
    op.drop_index(op.f("ix_guidance_items_section_path"), table_name="guidance_items")
    op.drop_index(op.f("ix_guidance_items_level3"), table_name="guidance_items")
    op.drop_index(op.f("ix_guidance_items_level2"), table_name="guidance_items")
    op.drop_index(op.f("ix_guidance_items_level1"), table_name="guidance_items")
    op.drop_index(op.f("ix_guidance_items_guidance_code"), table_name="guidance_items")
    op.drop_table("guidance_items")
