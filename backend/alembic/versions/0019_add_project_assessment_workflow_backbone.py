"""add project assessment workflow backbone

Revision ID: 0019_add_project_assessment_workflow_backbone
Revises: 0018_add_template_history_links
Create Date: 2026-04-27 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0019_add_project_assessment_workflow_backbone"
down_revision: Union[str, None] = "0018_add_template_history_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_assessment_tables",
        sa.Column("project_id", sa.String(length=36), nullable=False, comment="所属项目ID"),
        sa.Column("asset_id", sa.String(length=36), nullable=False, comment="所属资产ID"),
        sa.Column("source_workbook_id", sa.String(length=36), nullable=True, comment="来源主模板工作簿ID"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="项目测评表名称"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft", comment="测评表状态"),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0", comment="测评表项数量"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], name=op.f("fk_project_assessment_tables_asset_id_assets"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_project_assessment_tables_project_id_projects"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_workbook_id"], ["assessment_template_workbooks.id"], name=op.f("fk_project_assessment_tables_source_workbook_id_assessment_template_workbooks"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_assessment_tables")),
        sa.UniqueConstraint("project_id", "asset_id", name="uq_project_assessment_tables_project_id_asset_id"),
    )
    op.create_index(op.f("ix_project_assessment_tables_project_id"), "project_assessment_tables", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_assessment_tables_asset_id"), "project_assessment_tables", ["asset_id"], unique=False)
    op.create_index(op.f("ix_project_assessment_tables_source_workbook_id"), "project_assessment_tables", ["source_workbook_id"], unique=False)
    op.create_index(op.f("ix_project_assessment_tables_status"), "project_assessment_tables", ["status"], unique=False)

    op.create_table(
        "project_assessment_items",
        sa.Column("table_id", sa.String(length=36), nullable=False, comment="项目测评表ID"),
        sa.Column("project_id", sa.String(length=36), nullable=False, comment="所属项目ID"),
        sa.Column("asset_id", sa.String(length=36), nullable=False, comment="所属资产ID"),
        sa.Column("source_template_item_id", sa.String(length=36), nullable=True, comment="来源主模板项ID"),
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
        sa.Column("evidence_ids_json", sa.JSON(), nullable=True, comment="关联证据ID JSON"),
        sa.Column("evidence_facts_json", sa.JSON(), nullable=True, comment="证据事实快照JSON"),
        sa.Column("guidance_refs_json", sa.JSON(), nullable=True, comment="指导书引用JSON"),
        sa.Column("history_refs_json", sa.JSON(), nullable=True, comment="历史写法引用JSON"),
        sa.Column("draft_record_text", sa.Text(), nullable=True, comment="草稿结果记录"),
        sa.Column("draft_compliance_result", sa.String(length=100), nullable=True, comment="草稿符合情况"),
        sa.Column("final_record_text", sa.Text(), nullable=True, comment="最终结果记录"),
        sa.Column("final_compliance_result", sa.String(length=100), nullable=True, comment="最终符合情况"),
        sa.Column("confidence", sa.Float(), nullable=True, comment="生成置信度"),
        sa.Column("match_score", sa.Float(), nullable=True, comment="匹配得分"),
        sa.Column("match_reason_json", sa.JSON(), nullable=True, comment="匹配原因JSON"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending", comment="项目测评项状态"),
        sa.Column("review_comment", sa.Text(), nullable=True, comment="复核意见"),
        sa.Column("reviewed_by", sa.String(length=100), nullable=True, comment="复核人"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True, comment="复核时间"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], name=op.f("fk_project_assessment_items_asset_id_assets"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_project_assessment_items_project_id_projects"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_template_item_id"], ["assessment_template_items.id"], name=op.f("fk_project_assessment_items_source_template_item_id_assessment_template_items"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["table_id"], ["project_assessment_tables.id"], name=op.f("fk_project_assessment_items_table_id_project_assessment_tables"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_assessment_items")),
        sa.UniqueConstraint("table_id", "source_template_item_id", name="uq_project_assessment_items_table_id_source_template_item_id"),
    )
    op.create_index(op.f("ix_project_assessment_items_table_id"), "project_assessment_items", ["table_id"], unique=False)
    op.create_index(op.f("ix_project_assessment_items_project_id"), "project_assessment_items", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_assessment_items_asset_id"), "project_assessment_items", ["asset_id"], unique=False)
    op.create_index(op.f("ix_project_assessment_items_source_template_item_id"), "project_assessment_items", ["source_template_item_id"], unique=False)
    op.create_index(op.f("ix_project_assessment_items_sheet_name"), "project_assessment_items", ["sheet_name"], unique=False)
    op.create_index(op.f("ix_project_assessment_items_row_index"), "project_assessment_items", ["row_index"], unique=False)
    op.create_index(op.f("ix_project_assessment_items_control_point"), "project_assessment_items", ["control_point"], unique=False)
    op.create_index(op.f("ix_project_assessment_items_item_code"), "project_assessment_items", ["item_code"], unique=False)
    op.create_index(op.f("ix_project_assessment_items_object_type"), "project_assessment_items", ["object_type"], unique=False)
    op.create_index(op.f("ix_project_assessment_items_object_category"), "project_assessment_items", ["object_category"], unique=False)
    op.create_index(op.f("ix_project_assessment_items_status"), "project_assessment_items", ["status"], unique=False)

    op.create_table(
        "evidence_facts",
        sa.Column("project_id", sa.String(length=36), nullable=False, comment="所属项目ID"),
        sa.Column("asset_id", sa.String(length=36), nullable=True, comment="所属资产ID"),
        sa.Column("evidence_id", sa.String(length=36), nullable=False, comment="所属证据ID"),
        sa.Column("project_assessment_item_id", sa.String(length=36), nullable=True, comment="匹配项目测评项ID"),
        sa.Column("matched_template_item_id", sa.String(length=36), nullable=True, comment="匹配主模板项ID"),
        sa.Column("page_type", sa.String(length=100), nullable=True, comment="页面类型"),
        sa.Column("fact_group", sa.String(length=100), nullable=False, comment="事实分组"),
        sa.Column("fact_key", sa.String(length=100), nullable=False, comment="事实键"),
        sa.Column("fact_name", sa.String(length=255), nullable=False, comment="事实名称"),
        sa.Column("raw_value", sa.Text(), nullable=True, comment="原始事实值"),
        sa.Column("normalized_value", sa.Text(), nullable=True, comment="归一化事实值"),
        sa.Column("value_number", sa.Float(), nullable=True, comment="数值类型事实值"),
        sa.Column("value_bool", sa.Boolean(), nullable=True, comment="布尔类型事实值"),
        sa.Column("value_json", sa.JSON(), nullable=True, comment="JSON类型事实值"),
        sa.Column("source_text", sa.Text(), nullable=True, comment="来源文本"),
        sa.Column("source_page", sa.Integer(), nullable=True, comment="来源页码"),
        sa.Column("confidence", sa.Float(), nullable=True, comment="识别置信度"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="identified", comment="事实状态"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], name=op.f("fk_evidence_facts_asset_id_assets"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidences.id"], name=op.f("fk_evidence_facts_evidence_id_evidences"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matched_template_item_id"], ["assessment_template_items.id"], name=op.f("fk_evidence_facts_matched_template_item_id_assessment_template_items"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_assessment_item_id"], ["project_assessment_items.id"], name=op.f("fk_evidence_facts_project_assessment_item_id_project_assessment_items"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_evidence_facts_project_id_projects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_facts")),
    )
    op.create_index(op.f("ix_evidence_facts_project_id"), "evidence_facts", ["project_id"], unique=False)
    op.create_index(op.f("ix_evidence_facts_asset_id"), "evidence_facts", ["asset_id"], unique=False)
    op.create_index(op.f("ix_evidence_facts_evidence_id"), "evidence_facts", ["evidence_id"], unique=False)
    op.create_index(op.f("ix_evidence_facts_project_assessment_item_id"), "evidence_facts", ["project_assessment_item_id"], unique=False)
    op.create_index(op.f("ix_evidence_facts_matched_template_item_id"), "evidence_facts", ["matched_template_item_id"], unique=False)
    op.create_index(op.f("ix_evidence_facts_page_type"), "evidence_facts", ["page_type"], unique=False)
    op.create_index(op.f("ix_evidence_facts_fact_group"), "evidence_facts", ["fact_group"], unique=False)
    op.create_index(op.f("ix_evidence_facts_fact_key"), "evidence_facts", ["fact_key"], unique=False)
    op.create_index(op.f("ix_evidence_facts_status"), "evidence_facts", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evidence_facts_status"), table_name="evidence_facts")
    op.drop_index(op.f("ix_evidence_facts_fact_key"), table_name="evidence_facts")
    op.drop_index(op.f("ix_evidence_facts_fact_group"), table_name="evidence_facts")
    op.drop_index(op.f("ix_evidence_facts_page_type"), table_name="evidence_facts")
    op.drop_index(op.f("ix_evidence_facts_matched_template_item_id"), table_name="evidence_facts")
    op.drop_index(op.f("ix_evidence_facts_project_assessment_item_id"), table_name="evidence_facts")
    op.drop_index(op.f("ix_evidence_facts_evidence_id"), table_name="evidence_facts")
    op.drop_index(op.f("ix_evidence_facts_asset_id"), table_name="evidence_facts")
    op.drop_index(op.f("ix_evidence_facts_project_id"), table_name="evidence_facts")
    op.drop_table("evidence_facts")

    op.drop_index(op.f("ix_project_assessment_items_status"), table_name="project_assessment_items")
    op.drop_index(op.f("ix_project_assessment_items_object_category"), table_name="project_assessment_items")
    op.drop_index(op.f("ix_project_assessment_items_object_type"), table_name="project_assessment_items")
    op.drop_index(op.f("ix_project_assessment_items_item_code"), table_name="project_assessment_items")
    op.drop_index(op.f("ix_project_assessment_items_control_point"), table_name="project_assessment_items")
    op.drop_index(op.f("ix_project_assessment_items_row_index"), table_name="project_assessment_items")
    op.drop_index(op.f("ix_project_assessment_items_sheet_name"), table_name="project_assessment_items")
    op.drop_index(op.f("ix_project_assessment_items_source_template_item_id"), table_name="project_assessment_items")
    op.drop_index(op.f("ix_project_assessment_items_asset_id"), table_name="project_assessment_items")
    op.drop_index(op.f("ix_project_assessment_items_project_id"), table_name="project_assessment_items")
    op.drop_index(op.f("ix_project_assessment_items_table_id"), table_name="project_assessment_items")
    op.drop_table("project_assessment_items")

    op.drop_index(op.f("ix_project_assessment_tables_status"), table_name="project_assessment_tables")
    op.drop_index(op.f("ix_project_assessment_tables_source_workbook_id"), table_name="project_assessment_tables")
    op.drop_index(op.f("ix_project_assessment_tables_asset_id"), table_name="project_assessment_tables")
    op.drop_index(op.f("ix_project_assessment_tables_project_id"), table_name="project_assessment_tables")
    op.drop_table("project_assessment_tables")
