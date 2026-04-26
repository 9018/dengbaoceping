from __future__ import annotations

from collections import Counter

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.assessment_template import AssessmentTemplateItem, AssessmentTemplateSheet, AssessmentTemplateWorkbook


class AssessmentTemplateService:
    def list_workbooks(self, db: Session) -> list[AssessmentTemplateWorkbook]:
        return db.query(AssessmentTemplateWorkbook).order_by(AssessmentTemplateWorkbook.created_at.desc()).all()

    def get_workbook(self, db: Session, workbook_id: str) -> dict:
        workbook = db.get(AssessmentTemplateWorkbook, workbook_id)
        if not workbook:
            raise NotFoundException("ASSESSMENT_TEMPLATE_WORKBOOK_NOT_FOUND", "测评记录模板工作簿不存在")
        stats = self.build_workbook_stats(db, workbook_id)
        return {
            "id": workbook.id,
            "source_file": workbook.source_file,
            "name": workbook.name,
            "version": workbook.version,
            "sheet_count": workbook.sheet_count,
            "item_count": workbook.item_count,
            "created_at": workbook.created_at,
            "updated_at": workbook.updated_at,
            **stats,
        }

    def list_sheets(self, db: Session, workbook_id: str) -> list[AssessmentTemplateSheet]:
        self._require_workbook(db, workbook_id)
        return (
            db.query(AssessmentTemplateSheet)
            .filter(AssessmentTemplateSheet.workbook_id == workbook_id)
            .order_by(AssessmentTemplateSheet.sheet_name.asc(), AssessmentTemplateSheet.created_at.asc())
            .all()
        )

    def list_items(
        self,
        db: Session,
        *,
        workbook_id: str | None = None,
        sheet_name: str | None = None,
        object_type: str | None = None,
        object_category: str | None = None,
        control_point: str | None = None,
        item_code: str | None = None,
        keyword: str | None = None,
        page_type: str | None = None,
    ) -> list[AssessmentTemplateItem]:
        query = db.query(AssessmentTemplateItem)
        if workbook_id:
            query = query.filter(AssessmentTemplateItem.workbook_id == workbook_id)
        if sheet_name:
            query = query.filter(AssessmentTemplateItem.sheet_name == sheet_name)
        if object_type:
            query = query.filter(AssessmentTemplateItem.object_type == object_type)
        if object_category:
            query = query.filter(AssessmentTemplateItem.object_category == object_category)
        if control_point:
            query = query.filter(AssessmentTemplateItem.control_point.ilike(f"%{control_point}%"))
        if item_code:
            query = query.filter(AssessmentTemplateItem.item_code.ilike(f"%{item_code}%"))
        if keyword:
            normalized = f"%{keyword.lower()}%"
            query = query.filter(
                or_(
                    func.lower(func.coalesce(AssessmentTemplateItem.control_point, "")).like(normalized),
                    func.lower(func.coalesce(AssessmentTemplateItem.item_text, "")).like(normalized),
                    func.lower(func.coalesce(AssessmentTemplateItem.record_template, "")).like(normalized),
                    func.lower(func.coalesce(AssessmentTemplateItem.item_code, "")).like(normalized),
                    func.lower(func.coalesce(cast(AssessmentTemplateItem.evidence_keywords_json, String), "")).like(normalized),
                    func.lower(func.coalesce(cast(AssessmentTemplateItem.command_keywords_json, String), "")).like(normalized),
                )
            )
        if page_type:
            normalized_page_type = page_type.lower()
            items = query.order_by(AssessmentTemplateItem.sheet_name.asc(), AssessmentTemplateItem.row_index.asc()).all()
            return [item for item in items if normalized_page_type in [str(value).lower() for value in (item.page_types_json or [])]]
        return query.order_by(AssessmentTemplateItem.sheet_name.asc(), AssessmentTemplateItem.row_index.asc()).all()

    def build_workbook_stats(self, db: Session, workbook_id: str) -> dict:
        type_rows = (
            db.query(AssessmentTemplateSheet.object_type, func.count(AssessmentTemplateSheet.id))
            .filter(AssessmentTemplateSheet.workbook_id == workbook_id)
            .group_by(AssessmentTemplateSheet.object_type)
            .all()
        )
        category_rows = (
            db.query(AssessmentTemplateSheet.object_category, func.count(AssessmentTemplateSheet.id))
            .filter(AssessmentTemplateSheet.workbook_id == workbook_id)
            .group_by(AssessmentTemplateSheet.object_category)
            .all()
        )
        control_rows = (
            db.query(AssessmentTemplateItem.control_point, func.count(AssessmentTemplateItem.id))
            .filter(AssessmentTemplateItem.workbook_id == workbook_id)
            .group_by(AssessmentTemplateItem.control_point)
            .all()
        )
        return {
            "object_type_counts": self._group_rows(type_rows, "未分类"),
            "object_category_counts": self._group_rows(category_rows, "未分类"),
            "control_point_counts": self._group_rows(control_rows, "未标注"),
        }

    def _group_rows(self, rows: list[tuple[str | None, int]], fallback: str) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for key, total in rows:
            counts[key or fallback] += total
        return dict(counts)

    def _require_workbook(self, db: Session, workbook_id: str) -> AssessmentTemplateWorkbook:
        workbook = db.get(AssessmentTemplateWorkbook, workbook_id)
        if not workbook:
            raise NotFoundException("ASSESSMENT_TEMPLATE_WORKBOOK_NOT_FOUND", "测评记录模板工作簿不存在")
        return workbook
