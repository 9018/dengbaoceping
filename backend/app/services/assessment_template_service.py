from __future__ import annotations

from collections import Counter

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.assessment_template import AssessmentTemplateItem, AssessmentTemplateSheet, AssessmentTemplateWorkbook, TemplateGuidebookLink, TemplateHistoryLink
from app.models.evidence_fact import EvidenceFact
from app.models.project_assessment_table import ProjectAssessmentItem, ProjectAssessmentTable


class AssessmentTemplateService:
    def list_workbooks(self, db: Session, *, include_archived: bool = False) -> list[AssessmentTemplateWorkbook]:
        query = db.query(AssessmentTemplateWorkbook)
        if not include_archived:
            query = query.filter(AssessmentTemplateWorkbook.is_archived.is_(False))
        return query.order_by(AssessmentTemplateWorkbook.created_at.desc()).all()

    def list_workbooks_page(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        include_archived: bool = False,
    ) -> tuple[list[AssessmentTemplateWorkbook], int]:
        query = db.query(AssessmentTemplateWorkbook)
        if not include_archived:
            query = query.filter(AssessmentTemplateWorkbook.is_archived.is_(False))
        total = query.count()
        items = query.order_by(AssessmentTemplateWorkbook.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_workbook(self, db: Session, workbook_id: str) -> dict:
        workbook = db.get(AssessmentTemplateWorkbook, workbook_id)
        if not workbook:
            raise NotFoundException("ASSESSMENT_TEMPLATE_WORKBOOK_NOT_FOUND", "测评记录模板工作簿不存在")
        stats = self.build_workbook_stats(db, workbook_id)
        return {
            "id": workbook.id,
            "source_file": workbook.source_file,
            "source_file_hash": workbook.source_file_hash,
            "file_size": workbook.file_size,
            "import_batch_id": workbook.import_batch_id,
            "is_archived": workbook.is_archived,
            "name": workbook.name,
            "version": workbook.version,
            "sheet_count": workbook.sheet_count,
            "item_count": workbook.item_count,
            "created_at": workbook.created_at,
            "updated_at": workbook.updated_at,
            **stats,
        }

    def update_workbook(self, db: Session, workbook_id: str, *, name: str | None = None, version: str | None = None) -> AssessmentTemplateWorkbook:
        workbook = self._require_workbook(db, workbook_id)
        updates = {
            "name": name,
            "version": version,
        }
        if not any(value is not None for value in updates.values()):
            raise BadRequestException("ASSESSMENT_TEMPLATE_WORKBOOK_UPDATE_EMPTY", "请至少提供一个需要更新的字段")
        for field_name, value in updates.items():
            if value is not None:
                setattr(workbook, field_name, value.strip() if isinstance(value, str) else value)
        db.commit()
        db.refresh(workbook)
        return workbook

    def delete_workbook(self, db: Session, workbook_id: str, *, force: bool = False) -> dict:
        workbook = self._require_workbook(db, workbook_id)
        referenced_count = self._count_workbook_project_references(db, workbook.id)
        if referenced_count:
            if not force:
                raise ConflictException(
                    "TEMPLATE_WORKBOOK_IN_USE",
                    "模板工作簿已被项目测评表引用，无法直接删除",
                    details={"referenced_project_table_count": referenced_count},
                )
            workbook.is_archived = True
            db.commit()
            db.refresh(workbook)
            return {"id": workbook.id, "archived": True, "referenced_project_table_count": referenced_count}

        db.delete(workbook)
        db.commit()
        return {"id": workbook.id, "archived": False, "referenced_project_table_count": 0}

    def get_item(self, db: Session, item_id: str) -> AssessmentTemplateItem:
        item = db.get(AssessmentTemplateItem, item_id)
        if not item:
            raise NotFoundException("ASSESSMENT_TEMPLATE_ITEM_NOT_FOUND", "测评记录模板项不存在")
        return item

    def update_item(self, db: Session, item_id: str, **payload) -> AssessmentTemplateItem:
        item = self.get_item(db, item_id)
        updates = {key: value for key, value in payload.items() if value is not None}
        if not updates:
            raise BadRequestException("ASSESSMENT_TEMPLATE_ITEM_UPDATE_EMPTY", "请至少提供一个需要更新的字段")
        for field_name, value in updates.items():
            setattr(item, field_name, value.strip() if isinstance(value, str) else value)
        db.commit()
        db.refresh(item)
        return item

    def delete_item(self, db: Session, item_id: str) -> dict:
        item = self.get_item(db, item_id)
        referenced_project_item_count = self._count_item_project_references(db, item.id)
        if referenced_project_item_count:
            raise ConflictException(
                "TEMPLATE_ITEM_IN_USE",
                "模板项已被项目测评项引用，无法删除",
                details={"referenced_project_item_count": referenced_project_item_count},
            )
        linked_guidebook_count = db.query(func.count(TemplateGuidebookLink.id)).filter(TemplateGuidebookLink.template_item_id == item.id).scalar() or 0
        linked_history_count = db.query(func.count(TemplateHistoryLink.id)).filter(TemplateHistoryLink.template_item_id == item.id).scalar() or 0
        matched_fact_count = db.query(func.count(EvidenceFact.id)).filter(EvidenceFact.matched_template_item_id == item.id).scalar() or 0
        db.delete(item)
        self._refresh_workbook_counters(db, item.workbook_id)
        db.commit()
        return {
            "id": item.id,
            "linked_guidebook_count": linked_guidebook_count,
            "linked_history_count": linked_history_count,
            "matched_fact_count": matched_fact_count,
        }

    def list_sheets(self, db: Session, workbook_id: str) -> list[AssessmentTemplateSheet]:
        self._require_workbook(db, workbook_id)
        return self._sheets_query(db, workbook_id).order_by(AssessmentTemplateSheet.sheet_name.asc(), AssessmentTemplateSheet.created_at.asc()).all()

    def list_sheets_page(self, db: Session, workbook_id: str, *, page: int = 1, page_size: int = 50) -> tuple[list[AssessmentTemplateSheet], int]:
        self._require_workbook(db, workbook_id)
        query = self._sheets_query(db, workbook_id)
        total = query.count()
        items = query.order_by(AssessmentTemplateSheet.sheet_name.asc(), AssessmentTemplateSheet.created_at.asc()).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

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
        return self._items_query(
            db,
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            object_type=object_type,
            object_category=object_category,
            control_point=control_point,
            item_code=item_code,
            keyword=keyword,
            page_type=page_type,
        ).order_by(AssessmentTemplateItem.sheet_name.asc(), AssessmentTemplateItem.row_index.asc()).all()

    def list_items_page(
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
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AssessmentTemplateItem], int]:
        query = self._items_query(
            db,
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            object_type=object_type,
            object_category=object_category,
            control_point=control_point,
            item_code=item_code,
            keyword=keyword,
            page_type=page_type,
        )
        total = query.count()
        items = query.order_by(AssessmentTemplateItem.sheet_name.asc(), AssessmentTemplateItem.row_index.asc()).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

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

    def _items_query(
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
    ):
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
            query = query.filter(func.lower(func.coalesce(cast(AssessmentTemplateItem.page_types_json, String), "")).like(f"%{page_type.lower()}%"))
        return query

    def _sheets_query(self, db: Session, workbook_id: str):
        return db.query(AssessmentTemplateSheet).filter(AssessmentTemplateSheet.workbook_id == workbook_id)

    def _refresh_workbook_counters(self, db: Session, workbook_id: str) -> None:
        workbook = self._require_workbook(db, workbook_id)
        workbook.sheet_count = db.query(func.count(AssessmentTemplateSheet.id)).filter(AssessmentTemplateSheet.workbook_id == workbook_id).scalar() or 0
        workbook.item_count = db.query(func.count(AssessmentTemplateItem.id)).filter(AssessmentTemplateItem.workbook_id == workbook_id).scalar() or 0

    def _count_workbook_project_references(self, db: Session, workbook_id: str) -> int:
        return db.query(func.count(ProjectAssessmentTable.id)).filter(ProjectAssessmentTable.source_workbook_id == workbook_id).scalar() or 0

    def _count_item_project_references(self, db: Session, item_id: str) -> int:
        return db.query(func.count(ProjectAssessmentItem.id)).filter(ProjectAssessmentItem.source_template_item_id == item_id).scalar() or 0

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
