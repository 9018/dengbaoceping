"""add knowledge import batches and ocr metadata

Revision ID: 0020_add_knowledge_import_batches_and_ocr_metadata
Revises: 0019_add_project_assessment_workflow_backbone
Create Date: 2026-04-27 13:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0020_add_knowledge_import_batches_and_ocr_metadata"
down_revision: Union[str, None] = "0019_add_project_assessment_workflow_backbone"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_import_batches",
        sa.Column("library_type", sa.String(length=50), nullable=False, comment="知识库类型"),
        sa.Column("source_file", sa.String(length=255), nullable=True, comment="来源文件"),
        sa.Column("source_file_hash", sa.String(length=64), nullable=True, comment="来源文件哈希"),
        sa.Column("file_size", sa.Integer(), nullable=True, comment="文件大小"),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0", comment="导入条目数量"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending", comment="导入状态"),
        sa.Column("duplicate_of_id", sa.String(length=36), nullable=True, comment="重复批次ID"),
        sa.Column("import_mode", sa.String(length=50), nullable=True, comment="导入模式"),
        sa.Column("summary_json", sa.JSON(), nullable=True, comment="导入摘要JSON"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.ForeignKeyConstraint(["duplicate_of_id"], ["knowledge_import_batches.id"], name=op.f("fk_knowledge_import_batches_duplicate_of_id_knowledge_import_batches"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_import_batches")),
    )
    op.create_index(op.f("ix_knowledge_import_batches_library_type"), "knowledge_import_batches", ["library_type"], unique=False)
    op.create_index(op.f("ix_knowledge_import_batches_source_file_hash"), "knowledge_import_batches", ["source_file_hash"], unique=False)
    op.create_index(op.f("ix_knowledge_import_batches_status"), "knowledge_import_batches", ["status"], unique=False)
    op.create_index(op.f("ix_knowledge_import_batches_duplicate_of_id"), "knowledge_import_batches", ["duplicate_of_id"], unique=False)

    with op.batch_alter_table("assessment_template_workbooks") as batch_op:
        batch_op.add_column(sa.Column("source_file_hash", sa.String(length=64), nullable=True, comment="来源文件哈希"))
        batch_op.add_column(sa.Column("file_size", sa.Integer(), nullable=True, comment="来源文件大小"))
        batch_op.add_column(sa.Column("import_batch_id", sa.String(length=36), nullable=True, comment="导入批次ID"))
        batch_op.add_column(sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否归档"))
        batch_op.create_index(op.f("ix_assessment_template_workbooks_source_file_hash"), ["source_file_hash"], unique=False)
        batch_op.create_index(op.f("ix_assessment_template_workbooks_import_batch_id"), ["import_batch_id"], unique=False)
        batch_op.create_index(op.f("ix_assessment_template_workbooks_is_archived"), ["is_archived"], unique=False)
        batch_op.create_foreign_key(
            op.f("fk_assessment_template_workbooks_import_batch_id_knowledge_import_batches"),
            "knowledge_import_batches",
            ["import_batch_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("guidance_items") as batch_op:
        batch_op.add_column(sa.Column("source_file_hash", sa.String(length=64), nullable=True, comment="来源文件哈希"))
        batch_op.add_column(sa.Column("import_batch_id", sa.String(length=36), nullable=True, comment="导入批次ID"))
        batch_op.create_index(op.f("ix_guidance_items_source_file_hash"), ["source_file_hash"], unique=False)
        batch_op.create_index(op.f("ix_guidance_items_import_batch_id"), ["import_batch_id"], unique=False)
        batch_op.create_foreign_key(
            op.f("fk_guidance_items_import_batch_id_knowledge_import_batches"),
            "knowledge_import_batches",
            ["import_batch_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("history_records") as batch_op:
        batch_op.add_column(sa.Column("source_file_hash", sa.String(length=64), nullable=True, comment="来源文件哈希"))
        batch_op.add_column(sa.Column("import_batch_id", sa.String(length=36), nullable=True, comment="导入批次ID"))
        batch_op.create_index(op.f("ix_history_records_source_file_hash"), ["source_file_hash"], unique=False)
        batch_op.create_index(op.f("ix_history_records_import_batch_id"), ["import_batch_id"], unique=False)
        batch_op.create_foreign_key(
            op.f("fk_history_records_import_batch_id_knowledge_import_batches"),
            "knowledge_import_batches",
            ["import_batch_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("evidences") as batch_op:
        batch_op.add_column(sa.Column("ocr_error_message", sa.Text(), nullable=True, comment="OCR错误信息"))
        batch_op.add_column(sa.Column("ocr_error_json", sa.JSON(), nullable=True, comment="OCR错误详情JSON"))


def downgrade() -> None:
    with op.batch_alter_table("evidences") as batch_op:
        batch_op.drop_column("ocr_error_json")
        batch_op.drop_column("ocr_error_message")

    with op.batch_alter_table("history_records") as batch_op:
        batch_op.drop_constraint(op.f("fk_history_records_import_batch_id_knowledge_import_batches"), type_="foreignkey")
        batch_op.drop_index(op.f("ix_history_records_import_batch_id"))
        batch_op.drop_index(op.f("ix_history_records_source_file_hash"))
        batch_op.drop_column("import_batch_id")
        batch_op.drop_column("source_file_hash")

    with op.batch_alter_table("guidance_items") as batch_op:
        batch_op.drop_constraint(op.f("fk_guidance_items_import_batch_id_knowledge_import_batches"), type_="foreignkey")
        batch_op.drop_index(op.f("ix_guidance_items_import_batch_id"))
        batch_op.drop_index(op.f("ix_guidance_items_source_file_hash"))
        batch_op.drop_column("import_batch_id")
        batch_op.drop_column("source_file_hash")

    with op.batch_alter_table("assessment_template_workbooks") as batch_op:
        batch_op.drop_constraint(op.f("fk_assessment_template_workbooks_import_batch_id_knowledge_import_batches"), type_="foreignkey")
        batch_op.drop_index(op.f("ix_assessment_template_workbooks_is_archived"))
        batch_op.drop_index(op.f("ix_assessment_template_workbooks_import_batch_id"))
        batch_op.drop_index(op.f("ix_assessment_template_workbooks_source_file_hash"))
        batch_op.drop_column("is_archived")
        batch_op.drop_column("import_batch_id")
        batch_op.drop_column("file_size")
        batch_op.drop_column("source_file_hash")

    op.drop_index(op.f("ix_knowledge_import_batches_duplicate_of_id"), table_name="knowledge_import_batches")
    op.drop_index(op.f("ix_knowledge_import_batches_status"), table_name="knowledge_import_batches")
    op.drop_index(op.f("ix_knowledge_import_batches_source_file_hash"), table_name="knowledge_import_batches")
    op.drop_index(op.f("ix_knowledge_import_batches_library_type"), table_name="knowledge_import_batches")
    op.drop_table("knowledge_import_batches")
