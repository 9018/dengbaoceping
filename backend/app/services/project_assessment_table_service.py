from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.models.evidence_fact import EvidenceFact
from app.models.project_assessment_table import ProjectAssessmentItem, ProjectAssessmentTable
from app.repositories.asset_repository import AssetRepository
from app.repositories.evidence_fact_repository import EvidenceFactRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.history_record_repository import HistoryRecordRepository
from app.repositories.project_assessment_table_repository import ProjectAssessmentTableRepository
from app.repositories.project_repository import ProjectRepository
from app.services.assessment_template_service import AssessmentTemplateService
from app.services.guidance_service import GuidanceService
from app.services.template_item_match_service import TemplateItemMatchService


class ProjectAssessmentTableService:
    STAGE_TO_STEP = {
        "global_template_missing": ("setup", 0),
        "guidance_missing": ("setup", 0),
        "history_missing": ("setup", 0),
        "asset_missing": ("asset", 0),
        "table_missing": ("table", 1),
        "evidence_missing": ("evidence", 2),
        "ocr_pending": ("ocr", 2),
        "facts_missing": ("facts", 3),
        "item_match_missing": ("match", 4),
        "draft_missing": ("draft", 5),
        "confirm_missing": ("confirm", 6),
        "next_item": ("confirm", 6),
        "completed": ("export", 6),
    }

    def __init__(self) -> None:
        self.project_repository = ProjectRepository()
        self.asset_repository = AssetRepository()
        self.evidence_repository = EvidenceRepository()
        self.evidence_fact_repository = EvidenceFactRepository()
        self.repository = ProjectAssessmentTableRepository()
        self.template_service = AssessmentTemplateService()
        self.guidance_service = GuidanceService()
        self.history_record_repository = HistoryRecordRepository()
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

    def list_project_tables_page(self, db: Session, project_id: str, *, page: int = 1, page_size: int = 20) -> tuple[list[ProjectAssessmentTable], int]:
        self._require_project(db, project_id)
        return self.repository.list_by_project_page(db, project_id, page=page, page_size=page_size)

    def list_table_items(self, db: Session, table_id: str) -> list[ProjectAssessmentItem]:
        self._require_table(db, table_id)
        return self.repository.list_items(db, table_id)

    def list_table_items_page(self, db: Session, table_id: str, *, page: int = 1, page_size: int = 50) -> tuple[list[ProjectAssessmentItem], int]:
        self._require_table(db, table_id)
        return self.repository.list_items_page(db, table_id, page=page, page_size=page_size)

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

    def get_project_workflow_status(self, db: Session, project_id: str) -> dict[str, Any]:
        workflow = self.get_project_next_action(db, project_id)
        stats = workflow["stats"]
        return {
            "project_id": project_id,
            "status": workflow["stage"],
            "canNext": workflow["stage"] not in {"global_template_missing", "guidance_missing", "history_missing"},
            "summary": workflow["message"],
            "table_count": stats["table_count"],
            "item_count": stats["item_count"],
            "next_action": workflow,
            "stats": stats,
        }

    def get_project_next_action(self, db: Session, project_id: str) -> dict[str, Any]:
        self._require_project(db, project_id)

        workbooks = self.template_service.list_workbooks(db)
        guidance = self.guidance_service.list_items(db)
        history_total = self.history_record_repository.count(db)
        assets = self.asset_repository.list_matchable_by_project(db, project_id)
        tables = self.repository.list_by_project(db, project_id)
        items = self.repository.list_items_by_project(db, project_id)
        evidences = self.evidence_repository.list_by_project(db, project_id)

        evidence_by_id = {evidence.id: evidence for evidence in evidences}
        facts_by_evidence_id = {
            evidence.id: self.evidence_fact_repository.list_by_evidence(db, evidence.id)
            for evidence in evidences
        }
        matched_item_ids = {item.id for item in items if self._item_has_match(item)}
        stats = self._build_stats(assets, tables, items, evidences, facts_by_evidence_id, matched_item_ids)

        if not workbooks:
            return self._build_next_action(project_id, "global_template_missing", stats, message="请先导入全局测评模板")
        if guidance["total"] <= 0:
            return self._build_next_action(project_id, "guidance_missing", stats, message="请先导入指导书知识库")
        if history_total <= 0:
            return self._build_next_action(project_id, "history_missing", stats, message="请先导入历史测评记录")
        if not assets:
            return self._build_next_action(project_id, "asset_missing", stats, message="请先创建项目测试对象资产")

        table_assets = {table.asset_id for table in tables}
        missing_table_asset = next((asset for asset in assets if asset.id not in table_assets), None)
        if missing_table_asset is not None:
            return self._build_next_action(
                project_id,
                "table_missing",
                stats,
                asset_id=missing_table_asset.id,
                message=f"请先为资产 {missing_table_asset.filename} 生成项目测评表",
            )

        if not evidences:
            return self._build_next_action(project_id, "evidence_missing", stats, message="请先上传项目证据")

        ocr_target = next((evidence for evidence in evidences if not self._evidence_has_ocr_text(evidence)), None)
        if ocr_target is not None:
            return self._build_next_action(
                project_id,
                "ocr_pending",
                stats,
                evidence_id=ocr_target.id,
                message=f"请先完成证据 {ocr_target.title} 的 OCR 或手工录入文本",
            )

        facts_target = next((evidence for evidence in evidences if self._evidence_has_ocr_text(evidence) and not facts_by_evidence_id.get(evidence.id)), None)
        if facts_target is not None:
            return self._build_next_action(
                project_id,
                "facts_missing",
                stats,
                evidence_id=facts_target.id,
                message=f"请先识别证据 {facts_target.title} 的页面类型与事实",
            )

        match_target = self._find_item_match_missing(items, evidences, facts_by_evidence_id)
        if match_target is not None:
            item, evidence = match_target
            return self._build_next_action(
                project_id,
                "item_match_missing",
                stats,
                table_id=item.table_id,
                item_id=item.id,
                asset_id=item.asset_id,
                evidence_id=evidence.id if evidence else None,
                message=f"请先为测评项 {item.item_code or item.control_point or item.id} 匹配项目证据",
            )

        draft_target = self._find_draft_missing(items, evidence_by_id)
        if draft_target is not None:
            item, evidence_id = draft_target
            return self._build_next_action(
                project_id,
                "draft_missing",
                stats,
                table_id=item.table_id,
                item_id=item.id,
                asset_id=item.asset_id,
                evidence_id=evidence_id,
                message=f"请先为测评项 {item.item_code or item.control_point or item.id} 生成草稿",
            )

        confirm_target = self._find_confirm_missing(items, evidence_by_id)
        if confirm_target is not None:
            item, evidence_id = confirm_target
            return self._build_next_action(
                project_id,
                "confirm_missing",
                stats,
                table_id=item.table_id,
                item_id=item.id,
                asset_id=item.asset_id,
                evidence_id=evidence_id,
                message=f"请先人工确认测评项 {item.item_code or item.control_point or item.id}",
            )

        next_item = next((item for item in items if item.status != "confirmed"), None)
        if next_item is not None:
            evidence_id = self._first_evidence_id(next_item)
            return self._build_next_action(
                project_id,
                "next_item",
                stats,
                table_id=next_item.table_id,
                item_id=next_item.id,
                asset_id=next_item.asset_id,
                evidence_id=evidence_id,
                message=f"继续推进测评项 {next_item.item_code or next_item.control_point or next_item.id}",
            )

        return self._build_next_action(project_id, "completed", stats, message="项目测评流程已完成，可进入导出中心")

    def _build_stats(
        self,
        assets: list[Any],
        tables: list[ProjectAssessmentTable],
        items: list[ProjectAssessmentItem],
        evidences: list[Any],
        facts_by_evidence_id: dict[str, list[EvidenceFact]],
        matched_item_ids: set[str],
    ) -> dict[str, int]:
        ocr_completed_count = sum(1 for evidence in evidences if self._evidence_has_ocr_text(evidence))
        fact_count = sum(len(facts) for facts in facts_by_evidence_id.values())
        drafted_item_count = sum(1 for item in items if self._item_has_draft(item))
        confirmed_item_count = sum(1 for item in items if item.status == "confirmed")
        pending_review_count = sum(1 for item in items if item.status == "pending_review")
        pending_item_count = sum(1 for item in items if item.status not in {"confirmed", "drafted", "pending_review"})
        return {
            "asset_count": len(assets),
            "table_count": len(tables),
            "item_count": len(items),
            "evidence_count": len(evidences),
            "ocr_completed_count": ocr_completed_count,
            "fact_count": fact_count,
            "matched_item_count": len(matched_item_ids),
            "drafted_item_count": drafted_item_count,
            "confirmed_item_count": confirmed_item_count,
            "pending_item_count": pending_item_count,
            "pending_review_count": pending_review_count,
        }

    def _find_item_match_missing(self, items: list[ProjectAssessmentItem], evidences: list[Any], facts_by_evidence_id: dict[str, list[EvidenceFact]]):
        evidence = self._pick_fact_ready_evidence(evidences, facts_by_evidence_id)
        if evidence is None:
            return None
        for item in items:
            if not self._item_has_match(item):
                return item, evidence
        return None

    def _find_draft_missing(self, items: list[ProjectAssessmentItem], evidence_by_id: dict[str, Any]):
        for item in items:
            if not self._item_has_match(item) or self._item_has_draft(item):
                continue
            evidence_id = self._first_evidence_id(item)
            if evidence_id and evidence_id in evidence_by_id:
                return item, evidence_id
        return None

    def _find_confirm_missing(self, items: list[ProjectAssessmentItem], evidence_by_id: dict[str, Any]):
        for item in items:
            if item.status == "confirmed" or not self._item_has_draft(item):
                continue
            evidence_id = self._first_evidence_id(item)
            if evidence_id and evidence_id in evidence_by_id:
                return item, evidence_id
        return None

    def _pick_fact_ready_evidence(self, evidences: list[Any], facts_by_evidence_id: dict[str, list[EvidenceFact]]):
        for evidence in evidences:
            if self._evidence_has_ocr_text(evidence) and facts_by_evidence_id.get(evidence.id):
                return evidence
        return None

    def _evidence_has_ocr_text(self, evidence) -> bool:
        if evidence.text_content and str(evidence.text_content).strip():
            return True
        if evidence.ocr_status in {"completed", "completed_with_warning"}:
            return True
        if isinstance(evidence.ocr_result_json, dict) and str(evidence.ocr_result_json.get("full_text") or "").strip():
            return True
        return False

    def _item_has_match(self, item: ProjectAssessmentItem) -> bool:
        return bool(self._first_evidence_id(item))

    def _item_has_draft(self, item: ProjectAssessmentItem) -> bool:
        return bool((item.draft_record_text or "").strip()) or item.status in {"drafted", "pending_review", "confirmed"}

    def _first_evidence_id(self, item: ProjectAssessmentItem) -> str | None:
        raw_value = item.evidence_ids_json
        if isinstance(raw_value, list):
            for value in raw_value:
                if value:
                    return str(value)
        if isinstance(raw_value, str) and raw_value.strip():
            return raw_value.strip()
        return None

    def _build_next_action(
        self,
        project_id: str,
        stage: str,
        stats: dict[str, int],
        *,
        table_id: str | None = None,
        item_id: str | None = None,
        asset_id: str | None = None,
        evidence_id: str | None = None,
        message: str,
    ) -> dict[str, Any]:
        step_key, step_index = self.STAGE_TO_STEP[stage]
        route = "/setup-wizard" if step_key == "setup" else f"/projects/{project_id}/assessment-wizard"
        return {
            "project_id": project_id,
            "stage": stage,
            "step_key": step_key,
            "step_index": step_index,
            "route": route,
            "message": message,
            "table_id": table_id,
            "item_id": item_id,
            "asset_id": asset_id,
            "evidence_id": evidence_id,
            "stats": stats,
        }

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
