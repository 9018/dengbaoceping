from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.models.project_assessment_table import ProjectAssessmentItem, ProjectAssessmentTable
from app.repositories.asset_repository import AssetRepository
from app.repositories.project_assessment_table_repository import ProjectAssessmentTableRepository
from app.repositories.project_repository import ProjectRepository
from app.services.assessment_template_service import AssessmentTemplateService
from app.services.template_item_match_service import TemplateItemMatchService


class ProjectAssessmentTableService:
    def __init__(self) -> None:
        self.project_repository = ProjectRepository()
        self.asset_repository = AssetRepository()
        self.repository = ProjectAssessmentTableRepository()
        self.template_service = AssessmentTemplateService()
        self.template_match_service = TemplateItemMatchService()

    def generate_for_asset(self, db: Session, project_id: str, asset_id: str, force: bool = False) -> ProjectAssessmentTable:
        project = self.project_repository.get(db, project_id)
        if not project:
            raise NotFoundException("PROJECT_NOT_FOUND", "项目不存在")
        asset = self.asset_repository.get(db, asset_id)
        if not asset or asset.project_id != project_id:
            raise NotFoundException("ASSET_NOT_FOUND", "资产不存在")

        existing = self.repository.get_by_project_and_asset(db, project_id, asset_id)
        if existing and not force:
            raise ConflictException("PROJECT_ASSESSMENT_TABLE_ALREADY_EXISTS", "当前资产已生成项目测评表")
        if existing and force:
            self.repository.delete(db, existing)

        workbooks = self.template_service.list_workbooks(db)
        if not workbooks:
            raise NotFoundException("ASSESSMENT_TEMPLATE_WORKBOOK_NOT_FOUND", "测评记录模板工作簿不存在")
        workbook = workbooks[0]
        matched_items = self._select_template_items(db, workbook.id, asset)

        table = ProjectAssessmentTable(
            project_id=project_id,
            asset_id=asset_id,
            source_workbook_id=workbook.id,
            name=f"{project.name}-{asset.filename}-测评表",
            status="draft",
            item_count=len(matched_items),
        )
        db.add(table)
        db.flush()

        items = [self._build_project_item(table, asset, template_item) for template_item in matched_items]
        if items:
            db.add_all(items)
        db.commit()
        db.refresh(table)
        return table

    def list_project_tables(self, db: Session, project_id: str) -> list[ProjectAssessmentTable]:
        self._require_project(db, project_id)
        return self.repository.list_by_project(db, project_id)

    def list_table_items(self, db: Session, table_id: str) -> list[ProjectAssessmentItem]:
        self._require_table(db, table_id)
        return self.repository.list_items(db, table_id)

    def get_item(self, db: Session, item_id: str) -> ProjectAssessmentItem:
        item = self.repository.get_item(db, item_id)
        if not item:
            raise NotFoundException("PROJECT_ASSESSMENT_ITEM_NOT_FOUND", "项目测评项不存在")
        return item

    def update_item_draft(self, db: Session, item_id: str, payload: dict[str, Any]) -> ProjectAssessmentItem:
        item = self.get_item(db, item_id)
        for key in (
            "draft_record_text",
            "draft_compliance_result",
            "confidence",
            "match_score",
            "match_reason_json",
            "evidence_ids_json",
            "evidence_facts_json",
            "guidance_refs_json",
            "history_refs_json",
            "status",
        ):
            if key in payload:
                setattr(item, key, payload[key])
        return self.repository.update_item(db, item)

    def confirm_item(self, db: Session, item_id: str, *, final_record_text: str | None, final_compliance_result: str | None, review_comment: str | None = None, reviewed_by: str | None = None) -> ProjectAssessmentItem:
        item = self.get_item(db, item_id)
        item.final_record_text = final_record_text or item.draft_record_text
        item.final_compliance_result = final_compliance_result or item.draft_compliance_result
        item.review_comment = review_comment
        item.reviewed_by = reviewed_by
        item.reviewed_at = datetime.now(UTC)
        item.status = "confirmed"
        return self.repository.update_item(db, item)

    def _select_template_items(self, db: Session, workbook_id: str, asset) -> list:
        items = self.template_service.list_items(db, workbook_id=workbook_id)
        asset_type = asset.category
        matched = [item for item in items if self.template_match_service._infer_template_asset_type(item) == asset_type]
        if matched:
            return matched
        matched_by_category = [item for item in items if (item.object_category or "").lower() == (asset.category_label or "").lower()]
        return matched_by_category or items

    def _build_project_item(self, table: ProjectAssessmentTable, asset, template_item) -> ProjectAssessmentItem:
        return ProjectAssessmentItem(
            table_id=table.id,
            project_id=table.project_id,
            asset_id=asset.id,
            source_template_item_id=template_item.id,
            sheet_name=template_item.sheet_name,
            row_index=template_item.row_index,
            standard_type=template_item.standard_type,
            control_point=template_item.control_point,
            item_text=template_item.item_text,
            record_template=template_item.record_template,
            default_compliance_result=template_item.default_compliance_result,
            weight=template_item.weight,
            item_code=template_item.item_code,
            object_type=template_item.object_type,
            object_category=template_item.object_category,
            page_types_json=template_item.page_types_json,
            required_facts_json=template_item.required_facts_json,
            evidence_keywords_json=template_item.evidence_keywords_json,
            command_keywords_json=template_item.command_keywords_json,
            applicability_json=template_item.applicability_json,
            status="pending",
        )

    def _require_project(self, db: Session, project_id: str) -> None:
        if not self.project_repository.get(db, project_id):
            raise NotFoundException("PROJECT_NOT_FOUND", "项目不存在")

    def _require_table(self, db: Session, table_id: str) -> ProjectAssessmentTable:
        table = self.repository.get(db, table_id)
        if not table:
            raise NotFoundException("PROJECT_ASSESSMENT_TABLE_NOT_FOUND", "项目测评表不存在")
        return table
