"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-23 20:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("code", sa.String(length=64), nullable=True, comment="项目编码"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="项目名称"),
        sa.Column("project_type", sa.String(length=100), nullable=False, comment="项目类型"),
        sa.Column("status", sa.String(length=50), nullable=False, comment="项目状态"),
        sa.Column("description", sa.Text(), nullable=True, comment="项目说明"),
        sa.Column("storage_root", sa.String(length=500), nullable=True, comment="项目存储根目录"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
        sa.UniqueConstraint("code", name=op.f("uq_projects_code")),
    )
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)

    op.create_table(
        "assets",
        sa.Column("project_id", sa.String(length=36), nullable=False, comment="所属项目ID"),
        sa.Column("category", sa.String(length=50), nullable=False, comment="文件分类标识"),
        sa.Column("category_label", sa.String(length=100), nullable=False, comment="文件分类中文名称"),
        sa.Column("batch_no", sa.String(length=50), nullable=True, comment="上传批次号"),
        sa.Column("filename", sa.String(length=255), nullable=False, comment="文件名称"),
        sa.Column("file_ext", sa.String(length=20), nullable=True, comment="文件扩展名"),
        sa.Column("mime_type", sa.String(length=100), nullable=True, comment="文件MIME类型"),
        sa.Column("relative_path", sa.String(length=500), nullable=False, comment="相对存储路径"),
        sa.Column("absolute_path", sa.String(length=1000), nullable=True, comment="绝对存储路径"),
        sa.Column("file_size", sa.BigInteger(), nullable=True, comment="文件大小字节数"),
        sa.Column("file_sha256", sa.String(length=64), nullable=True, comment="文件SHA256摘要"),
        sa.Column("file_mtime", sa.DateTime(timezone=True), nullable=True, comment="文件最后修改时间"),
        sa.Column("source", sa.String(length=50), nullable=True, comment="文件来源"),
        sa.Column("ingest_status", sa.String(length=50), nullable=False, comment="入库处理状态"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_assets_project_id_projects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assets")),
        sa.UniqueConstraint("file_sha256", name=op.f("uq_assets_file_sha256")),
        sa.UniqueConstraint("relative_path", name=op.f("uq_assets_relative_path")),
    )
    op.create_index(op.f("ix_assets_batch_no"), "assets", ["batch_no"], unique=False)
    op.create_index(op.f("ix_assets_category"), "assets", ["category"], unique=False)
    op.create_index(op.f("ix_assets_project_id"), "assets", ["project_id"], unique=False)

    op.create_table(
        "evidences",
        sa.Column("project_id", sa.String(length=36), nullable=False, comment="所属项目ID"),
        sa.Column("asset_id", sa.String(length=36), nullable=True, comment="关联文件资产ID"),
        sa.Column("evidence_type", sa.String(length=50), nullable=False, comment="证据类型"),
        sa.Column("title", sa.String(length=255), nullable=False, comment="证据标题"),
        sa.Column("summary", sa.Text(), nullable=True, comment="证据摘要"),
        sa.Column("text_content", sa.Text(), nullable=True, comment="证据正文或抽取文本"),
        sa.Column("device", sa.String(length=255), nullable=True, comment="关联设备名称"),
        sa.Column("ports_json", sa.JSON(), nullable=True, comment="端口或网络信息JSON"),
        sa.Column("evidence_time", sa.DateTime(timezone=True), nullable=True, comment="证据时间"),
        sa.Column("tags_json", sa.JSON(), nullable=True, comment="证据标签JSON"),
        sa.Column("source_ref", sa.String(length=255), nullable=True, comment="来源引用标识"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], name=op.f("fk_evidences_asset_id_assets"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_evidences_project_id_projects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidences")),
    )
    op.create_index(op.f("ix_evidences_asset_id"), "evidences", ["asset_id"], unique=False)
    op.create_index(op.f("ix_evidences_evidence_time"), "evidences", ["evidence_time"], unique=False)
    op.create_index(op.f("ix_evidences_evidence_type"), "evidences", ["evidence_type"], unique=False)
    op.create_index(op.f("ix_evidences_project_id"), "evidences", ["project_id"], unique=False)

    op.create_table(
        "templates",
        sa.Column("project_id", sa.String(length=36), nullable=True, comment="所属项目ID"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="模板名称"),
        sa.Column("template_type", sa.String(length=50), nullable=False, comment="模板类型"),
        sa.Column("extension_type", sa.String(length=50), nullable=True, comment="扩展类型"),
        sa.Column("domain", sa.String(length=100), nullable=True, comment="领域名称"),
        sa.Column("level2", sa.String(length=255), nullable=True, comment="关联二级指标"),
        sa.Column("version", sa.String(length=50), nullable=True, comment="模板版本"),
        sa.Column("description", sa.Text(), nullable=True, comment="模板说明"),
        sa.Column("source_asset_id", sa.String(length=36), nullable=True, comment="来源文件资产ID"),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, comment="是否系统内置"),
        sa.Column("is_active", sa.Boolean(), nullable=False, comment="是否启用"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_templates_project_id_projects"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_asset_id"], ["assets.id"], name=op.f("fk_templates_source_asset_id_assets"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_templates")),
    )
    op.create_index(op.f("ix_templates_extension_type"), "templates", ["extension_type"], unique=False)
    op.create_index(op.f("ix_templates_name"), "templates", ["name"], unique=False)
    op.create_index(op.f("ix_templates_project_id"), "templates", ["project_id"], unique=False)
    op.create_index(op.f("ix_templates_source_asset_id"), "templates", ["source_asset_id"], unique=False)
    op.create_index(op.f("ix_templates_template_type"), "templates", ["template_type"], unique=False)

    op.create_table(
        "evaluation_items",
        sa.Column("template_id", sa.String(length=36), nullable=False, comment="所属模板ID"),
        sa.Column("domain", sa.String(length=100), nullable=True, comment="归属领域"),
        sa.Column("level1", sa.String(length=255), nullable=True, comment="一级指标"),
        sa.Column("level2", sa.String(length=255), nullable=False, comment="二级指标"),
        sa.Column("level3", sa.String(length=500), nullable=False, comment="三级指标"),
        sa.Column("extension_type", sa.String(length=50), nullable=False, comment="扩展类型"),
        sa.Column("route_domain", sa.String(length=100), nullable=True, comment="路由领域"),
        sa.Column("source_template_name", sa.String(length=255), nullable=True, comment="来源模板名称"),
        sa.Column("source_sheet_name", sa.String(length=255), nullable=True, comment="来源工作表名称"),
        sa.Column("sort_order", sa.Integer(), nullable=True, comment="排序序号"),
        sa.Column("is_active", sa.Boolean(), nullable=False, comment="是否启用"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["template_id"], ["templates.id"], name=op.f("fk_evaluation_items_template_id_templates"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_items")),
        sa.UniqueConstraint("template_id", "extension_type", "level2", "level3", name="uq_evaluation_items_template_extension_level2_level3"),
    )
    op.create_index(op.f("ix_evaluation_items_domain"), "evaluation_items", ["domain"], unique=False)
    op.create_index(op.f("ix_evaluation_items_extension_type"), "evaluation_items", ["extension_type"], unique=False)
    op.create_index(op.f("ix_evaluation_items_level2"), "evaluation_items", ["level2"], unique=False)
    op.create_index(op.f("ix_evaluation_items_route_domain"), "evaluation_items", ["route_domain"], unique=False)
    op.create_index(op.f("ix_evaluation_items_template_id"), "evaluation_items", ["template_id"], unique=False)

    op.create_table(
        "evaluation_records",
        sa.Column("project_id", sa.String(length=36), nullable=False, comment="所属项目ID"),
        sa.Column("template_id", sa.String(length=36), nullable=True, comment="关联模板ID"),
        sa.Column("evaluation_item_id", sa.String(length=36), nullable=True, comment="关联测评项ID"),
        sa.Column("asset_id", sa.String(length=36), nullable=True, comment="关联文件资产ID"),
        sa.Column("record_no", sa.String(length=100), nullable=True, comment="记录编号"),
        sa.Column("sheet_name", sa.String(length=255), nullable=True, comment="来源工作表名称"),
        sa.Column("indicator_l1", sa.String(length=255), nullable=True, comment="一级指标"),
        sa.Column("indicator_l2", sa.String(length=255), nullable=True, comment="二级指标"),
        sa.Column("indicator_l3", sa.String(length=500), nullable=True, comment="三级指标"),
        sa.Column("record_text", sa.Text(), nullable=True, comment="测评记录内容"),
        sa.Column("conclusion", sa.String(length=255), nullable=True, comment="结论"),
        sa.Column("risk_level", sa.String(length=100), nullable=True, comment="风险等级"),
        sa.Column("suggestion", sa.Text(), nullable=True, comment="整改建议"),
        sa.Column("status", sa.String(length=50), nullable=False, comment="记录状态"),
        sa.Column("source_type", sa.String(length=50), nullable=False, comment="来源类型"),
        sa.Column("source_row_no", sa.Integer(), nullable=True, comment="来源行号"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], name=op.f("fk_evaluation_records_asset_id_assets"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["evaluation_item_id"], ["evaluation_items.id"], name=op.f("fk_evaluation_records_evaluation_item_id_evaluation_items"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_evaluation_records_project_id_projects"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["templates.id"], name=op.f("fk_evaluation_records_template_id_templates"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_records")),
    )
    op.create_index(op.f("ix_evaluation_records_asset_id"), "evaluation_records", ["asset_id"], unique=False)
    op.create_index(op.f("ix_evaluation_records_evaluation_item_id"), "evaluation_records", ["evaluation_item_id"], unique=False)
    op.create_index(op.f("ix_evaluation_records_indicator_l2"), "evaluation_records", ["indicator_l2"], unique=False)
    op.create_index(op.f("ix_evaluation_records_project_id"), "evaluation_records", ["project_id"], unique=False)
    op.create_index(op.f("ix_evaluation_records_sheet_name"), "evaluation_records", ["sheet_name"], unique=False)
    op.create_index(op.f("ix_evaluation_records_source_type"), "evaluation_records", ["source_type"], unique=False)
    op.create_index(op.f("ix_evaluation_records_template_id"), "evaluation_records", ["template_id"], unique=False)

    op.create_table(
        "extracted_fields",
        sa.Column("project_id", sa.String(length=36), nullable=False, comment="所属项目ID"),
        sa.Column("asset_id", sa.String(length=36), nullable=True, comment="关联文件资产ID"),
        sa.Column("evidence_id", sa.String(length=36), nullable=True, comment="关联证据ID"),
        sa.Column("template_id", sa.String(length=36), nullable=True, comment="关联模板ID"),
        sa.Column("record_id", sa.String(length=36), nullable=True, comment="关联测评记录ID"),
        sa.Column("field_group", sa.String(length=100), nullable=False, comment="字段分组"),
        sa.Column("field_name", sa.String(length=100), nullable=False, comment="字段名称"),
        sa.Column("field_value_text", sa.Text(), nullable=True, comment="文本类型字段值"),
        sa.Column("field_value_number", sa.Float(), nullable=True, comment="数值类型字段值"),
        sa.Column("field_value_bool", sa.Boolean(), nullable=True, comment="布尔类型字段值"),
        sa.Column("field_value_json", sa.JSON(), nullable=True, comment="JSON类型字段值"),
        sa.Column("source_page", sa.Integer(), nullable=True, comment="来源页码"),
        sa.Column("source_sheet", sa.String(length=255), nullable=True, comment="来源工作表"),
        sa.Column("source_row", sa.Integer(), nullable=True, comment="来源行号"),
        sa.Column("confidence", sa.Float(), nullable=True, comment="抽取置信度"),
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], name=op.f("fk_extracted_fields_asset_id_assets"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidences.id"], name=op.f("fk_extracted_fields_evidence_id_evidences"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_extracted_fields_project_id_projects"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["record_id"], ["evaluation_records.id"], name=op.f("fk_extracted_fields_record_id_evaluation_records"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["template_id"], ["templates.id"], name=op.f("fk_extracted_fields_template_id_templates"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extracted_fields")),
    )
    op.create_index(op.f("ix_extracted_fields_asset_id"), "extracted_fields", ["asset_id"], unique=False)
    op.create_index(op.f("ix_extracted_fields_evidence_id"), "extracted_fields", ["evidence_id"], unique=False)
    op.create_index(op.f("ix_extracted_fields_field_group"), "extracted_fields", ["field_group"], unique=False)
    op.create_index(op.f("ix_extracted_fields_field_name"), "extracted_fields", ["field_name"], unique=False)
    op.create_index(op.f("ix_extracted_fields_project_id"), "extracted_fields", ["project_id"], unique=False)
    op.create_index(op.f("ix_extracted_fields_record_id"), "extracted_fields", ["record_id"], unique=False)
    op.create_index(op.f("ix_extracted_fields_template_id"), "extracted_fields", ["template_id"], unique=False)

    op.create_table(
        "evaluation_record_evidences",
        sa.Column("evaluation_record_id", sa.String(length=36), nullable=False, comment="测评记录ID"),
        sa.Column("evidence_id", sa.String(length=36), nullable=False, comment="证据ID"),
        sa.Column("relation_type", sa.String(length=50), nullable=False, comment="关联类型"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.ForeignKeyConstraint(["evaluation_record_id"], ["evaluation_records.id"], name=op.f("fk_evaluation_record_evidences_evaluation_record_id_evaluation_records"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidences.id"], name=op.f("fk_evaluation_record_evidences_evidence_id_evidences"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("evaluation_record_id", "evidence_id", name="pk_evaluation_record_evidences"),
    )
    op.create_index(op.f("ix_evaluation_record_evidences_relation_type"), "evaluation_record_evidences", ["relation_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_record_evidences_relation_type"), table_name="evaluation_record_evidences")
    op.drop_table("evaluation_record_evidences")
    op.drop_index(op.f("ix_extracted_fields_template_id"), table_name="extracted_fields")
    op.drop_index(op.f("ix_extracted_fields_record_id"), table_name="extracted_fields")
    op.drop_index(op.f("ix_extracted_fields_project_id"), table_name="extracted_fields")
    op.drop_index(op.f("ix_extracted_fields_field_name"), table_name="extracted_fields")
    op.drop_index(op.f("ix_extracted_fields_field_group"), table_name="extracted_fields")
    op.drop_index(op.f("ix_extracted_fields_evidence_id"), table_name="extracted_fields")
    op.drop_index(op.f("ix_extracted_fields_asset_id"), table_name="extracted_fields")
    op.drop_table("extracted_fields")
    op.drop_index(op.f("ix_evaluation_records_template_id"), table_name="evaluation_records")
    op.drop_index(op.f("ix_evaluation_records_source_type"), table_name="evaluation_records")
    op.drop_index(op.f("ix_evaluation_records_sheet_name"), table_name="evaluation_records")
    op.drop_index(op.f("ix_evaluation_records_project_id"), table_name="evaluation_records")
    op.drop_index(op.f("ix_evaluation_records_indicator_l2"), table_name="evaluation_records")
    op.drop_index(op.f("ix_evaluation_records_evaluation_item_id"), table_name="evaluation_records")
    op.drop_index(op.f("ix_evaluation_records_asset_id"), table_name="evaluation_records")
    op.drop_table("evaluation_records")
    op.drop_index(op.f("ix_evaluation_items_template_id"), table_name="evaluation_items")
    op.drop_index(op.f("ix_evaluation_items_route_domain"), table_name="evaluation_items")
    op.drop_index(op.f("ix_evaluation_items_level2"), table_name="evaluation_items")
    op.drop_index(op.f("ix_evaluation_items_extension_type"), table_name="evaluation_items")
    op.drop_index(op.f("ix_evaluation_items_domain"), table_name="evaluation_items")
    op.drop_table("evaluation_items")
    op.drop_index(op.f("ix_templates_template_type"), table_name="templates")
    op.drop_index(op.f("ix_templates_source_asset_id"), table_name="templates")
    op.drop_index(op.f("ix_templates_project_id"), table_name="templates")
    op.drop_index(op.f("ix_templates_name"), table_name="templates")
    op.drop_index(op.f("ix_templates_extension_type"), table_name="templates")
    op.drop_table("templates")
    op.drop_index(op.f("ix_evidences_project_id"), table_name="evidences")
    op.drop_index(op.f("ix_evidences_evidence_type"), table_name="evidences")
    op.drop_index(op.f("ix_evidences_evidence_time"), table_name="evidences")
    op.drop_index(op.f("ix_evidences_asset_id"), table_name="evidences")
    op.drop_table("evidences")
    op.drop_index(op.f("ix_assets_project_id"), table_name="assets")
    op.drop_index(op.f("ix_assets_category"), table_name="assets")
    op.drop_index(op.f("ix_assets_batch_no"), table_name="assets")
    op.drop_table("assets")
    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.drop_table("projects")
