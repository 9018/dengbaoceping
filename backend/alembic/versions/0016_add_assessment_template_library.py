"""add assessment template library

Revision ID: 0016_add_assessment_template_library
Revises: 0015_add_project_template_workbook_fields
Create Date: 2026-04-26 20:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0016_add_assessment_template_library"
down_revision: Union[str, None] = "0015_add_project_template_workbook_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assessment_template_workbooks",
        sa.Column("source_file", sa.String(length=255), nullable=False, comment="来源文件"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="模板名称"),
        sa.Column("version", sa.String(length=100), nullable=True, comment="模板版本"),
        sa.Column("sheet_count", sa.Integer(), nullable=False, server_default="0", comment="工作表数量"),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0", comment="模板项数量"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessment_template_workbooks")),
    )
    op.create_index(op.f("ix_assessment_template_workbooks_name"), "assessment_template_workbooks", ["name"], unique=False)
    op.create_index(op.f("ix_assessment_template_workbooks_source_file"), "assessment_template_workbooks", ["source_file"], unique=False)
    op.create_index(op.f("ix_assessment_template_workbooks_version"), "assessment_template_workbooks", ["version"], unique=False)

    op.create_table(
        "assessment_template_sheets",
        sa.Column("workbook_id", sa.String(length=36), nullable=False, comment="模板工作簿ID"),
        sa.Column("sheet_name", sa.String(length=255), nullable=False, comment="工作表名称"),
        sa.Column("object_type", sa.String(length=100), nullable=True, comment="对象类型"),
        sa.Column("object_category", sa.String(length=100), nullable=True, comment="对象分类"),
        sa.Column("object_subtype", sa.String(length=100), nullable=True, comment="对象子类型"),
        sa.Column("is_physical", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否物理环境"),
        sa.Column("is_network", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否网络对象"),
        sa.Column("is_security_device", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否安全设备"),
        sa.Column("is_server", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否服务器"),
        sa.Column("is_database", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否数据库"),
        sa.Column("is_middleware", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否中间件"),
        sa.Column("is_application", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否应用系统"),
        sa.Column("is_data_object", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否数据对象"),
        sa.Column("is_management", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否管理对象"),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0", comment="解析行数"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.ForeignKeyConstraint(["workbook_id"], ["assessment_template_workbooks.id"], name=op.f("fk_assessment_template_sheets_workbook_id_assessment_template_workbooks"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessment_template_sheets")),
    )
    op.create_index(op.f("ix_assessment_template_sheets_object_category"), "assessment_template_sheets", ["object_category"], unique=False)
    op.create_index(op.f("ix_assessment_template_sheets_object_subtype"), "assessment_template_sheets", ["object_subtype"], unique=False)
    op.create_index(op.f("ix_assessment_template_sheets_object_type"), "assessment_template_sheets", ["object_type"], unique=False)
    op.create_index(op.f("ix_assessment_template_sheets_sheet_name"), "assessment_template_sheets", ["sheet_name"], unique=False)
    op.create_index(op.f("ix_assessment_template_sheets_workbook_id"), "assessment_template_sheets", ["workbook_id"], unique=False)

    op.create_table(
        "assessment_template_items",
        sa.Column("workbook_id", sa.String(length=36), nullable=False, comment="模板工作簿ID"),
        sa.Column("sheet_id", sa.String(length=36), nullable=False, comment="模板工作表ID"),
        sa.Column("sheet_name", sa.String(length=255), nullable=False, comment="工作表名称"),
        sa.Column("row_index", sa.Integer(), nullable=False, comment="来源行号"),
        sa.Column("standard_type", sa.String(length=255), nullable=True, comment="扩展标准"),
        sa.Column("control_point", sa.String(length=1000), nullable=True, comment="控制点"),
        sa.Column("item_text", sa.String(length=1000), nullable=True, comment="测评项"),
        sa.Column("record_template", sa.Text(), nullable=True, comment="结果记录模板"),
        sa.Column("default_compliance_result", sa.String(length=100), nullable=True, comment="默认符合情况"),
        sa.Column("weight", sa.Float(), nullable=True, comment="权重/分值"),
        sa.Column("item_code", sa.String(length=100), nullable=True, comment="编号"),
        sa.Column("object_type", sa.String(length=100), nullable=True, comment="对象类型"),
        sa.Column("object_category", sa.String(length=100), nullable=True, comment="对象分类"),
        sa.Column("page_types_json", sa.JSON(), nullable=True, comment="页面类型JSON"),
        sa.Column("required_facts_json", sa.JSON(), nullable=True, comment="必备事实JSON"),
        sa.Column("evidence_keywords_json", sa.JSON(), nullable=True, comment="证据关键词JSON"),
        sa.Column("command_keywords_json", sa.JSON(), nullable=True, comment="命令关键词JSON"),
        sa.Column("applicability_json", sa.JSON(), nullable=True, comment="适用范围JSON"),
        sa.Column("raw_row_json", sa.JSON(), nullable=True, comment="原始行JSON"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.ForeignKeyConstraint(["sheet_id"], ["assessment_template_sheets.id"], name=op.f("fk_assessment_template_items_sheet_id_assessment_template_sheets"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workbook_id"], ["assessment_template_workbooks.id"], name=op.f("fk_assessment_template_items_workbook_id_assessment_template_workbooks"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessment_template_items")),
    )
    op.create_index(op.f("ix_assessment_template_items_control_point"), "assessment_template_items", ["control_point"], unique=False)
    op.create_index(op.f("ix_assessment_template_items_item_code"), "assessment_template_items", ["item_code"], unique=False)
    op.create_index(op.f("ix_assessment_template_items_object_category"), "assessment_template_items", ["object_category"], unique=False)
    op.create_index(op.f("ix_assessment_template_items_object_type"), "assessment_template_items", ["object_type"], unique=False)
    op.create_index(op.f("ix_assessment_template_items_row_index"), "assessment_template_items", ["row_index"], unique=False)
    op.create_index(op.f("ix_assessment_template_items_sheet_id"), "assessment_template_items", ["sheet_id"], unique=False)
    op.create_index(op.f("ix_assessment_template_items_sheet_name"), "assessment_template_items", ["sheet_name"], unique=False)
    op.create_index(op.f("ix_assessment_template_items_workbook_id"), "assessment_template_items", ["workbook_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_assessment_template_items_workbook_id"), table_name="assessment_template_items")
    op.drop_index(op.f("ix_assessment_template_items_sheet_name"), table_name="assessment_template_items")
    op.drop_index(op.f("ix_assessment_template_items_sheet_id"), table_name="assessment_template_items")
    op.drop_index(op.f("ix_assessment_template_items_row_index"), table_name="assessment_template_items")
    op.drop_index(op.f("ix_assessment_template_items_object_type"), table_name="assessment_template_items")
    op.drop_index(op.f("ix_assessment_template_items_object_category"), table_name="assessment_template_items")
    op.drop_index(op.f("ix_assessment_template_items_item_code"), table_name="assessment_template_items")
    op.drop_index(op.f("ix_assessment_template_items_control_point"), table_name="assessment_template_items")
    op.drop_table("assessment_template_items")

    op.drop_index(op.f("ix_assessment_template_sheets_workbook_id"), table_name="assessment_template_sheets")
    op.drop_index(op.f("ix_assessment_template_sheets_sheet_name"), table_name="assessment_template_sheets")
    op.drop_index(op.f("ix_assessment_template_sheets_object_type"), table_name="assessment_template_sheets")
    op.drop_index(op.f("ix_assessment_template_sheets_object_subtype"), table_name="assessment_template_sheets")
    op.drop_index(op.f("ix_assessment_template_sheets_object_category"), table_name="assessment_template_sheets")
    op.drop_table("assessment_template_sheets")

    op.drop_index(op.f("ix_assessment_template_workbooks_version"), table_name="assessment_template_workbooks")
    op.drop_index(op.f("ix_assessment_template_workbooks_source_file"), table_name="assessment_template_workbooks")
    op.drop_index(op.f("ix_assessment_template_workbooks_name"), table_name="assessment_template_workbooks")
    op.drop_table("assessment_template_workbooks")
