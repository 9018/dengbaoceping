from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.assessment_template import TemplateGuidebookLink
from app.models.evidence import Evidence
from app.models.guidance_history_link import GuidanceHistoryLink
from app.models.guidance_item import GuidanceItem
from app.models.knowledge_import_batch import KnowledgeImportBatch
from app.services.guidance_parser import GuidanceParser


class GuidanceService:
    LIBRARY_TYPE = "guidance"

    def __init__(self) -> None:
        self.parser = GuidanceParser()

    @property
    def source_file(self) -> str:
        return "md/指导书.md"

    @property
    def guidance_path(self) -> Path:
        return Path(settings.GUIDANCE_FILE_PATH)

    def get_library_status(self, db: Session) -> dict:
        file_info = self._read_file_state()
        total = self._count_items(db)
        return {
            "source_file": self.source_file,
            "absolute_path": str(self.guidance_path),
            "file_exists": file_info["file_exists"],
            "file_empty": file_info["file_empty"],
            "file_message": file_info["message"],
            "imported": total > 0,
            "total": total,
        }

    def import_markdown(self, db: Session) -> dict:
        file_info = self._read_file_state(raise_on_error=True)
        if file_info["file_empty"]:
            raise BadRequestException("GUIDANCE_MD_EMPTY", "指导书.md 当前为空，请先补充内容")

        content = self.guidance_path.read_text(encoding="utf-8")
        source_file_hash = self._build_source_file_hash(content)
        latest_batch = self._find_latest_batch(db)
        duplicate = latest_batch is not None and latest_batch.source_file_hash == source_file_hash
        current_total = self._count_items(db)
        batch = KnowledgeImportBatch(
            library_type=self.LIBRARY_TYPE,
            source_file=self.source_file,
            source_file_hash=source_file_hash,
            file_size=len(content.encode("utf-8")),
            item_count=current_total,
            status="pending",
            duplicate_of_id=latest_batch.id if duplicate and latest_batch else None,
            import_mode="upsert",
        )
        db.add(batch)
        db.flush()

        if duplicate:
            batch.status = "skipped"
            batch.summary_json = {
                "imported_count": 0,
                "updated_count": 0,
                "skipped_count": current_total,
                "deleted_count": 0,
            }
            db.commit()
            return {
                **self.get_library_status(db),
                "batch_id": batch.id,
                "source_file_hash": source_file_hash,
                "imported_count": 0,
                "updated_count": 0,
                "skipped_count": current_total,
                "deleted_count": 0,
                "duplicate": True,
                "duplicate_of_id": batch.duplicate_of_id,
                "status": batch.status,
            }

        sections = self.parser.parse(self.guidance_path, self.source_file)
        if not sections:
            raise BadRequestException("GUIDANCE_MD_NO_SECTIONS", "指导书未识别到可导入的 Markdown 标题章节")

        existing_items = {
            item.guidance_code: item
            for item in db.query(GuidanceItem).filter(GuidanceItem.source_file == self.source_file).all()
        }
        next_codes = {section.guidance_code for section in sections}
        imported_count = 0
        updated_count = 0
        for section in sections:
            payload = asdict(section)
            payload["source_file_hash"] = source_file_hash
            payload["import_batch_id"] = batch.id
            existing = existing_items.get(section.guidance_code)
            if existing is None:
                db.add(GuidanceItem(**payload))
                imported_count += 1
                continue
            for field_name, value in payload.items():
                setattr(existing, field_name, value)
            updated_count += 1

        deleted_count = 0
        stale_items = [item for code, item in existing_items.items() if code not in next_codes]
        for stale_item in stale_items:
            db.delete(stale_item)
            deleted_count += 1

        batch.item_count = len(sections)
        batch.status = "imported"
        batch.summary_json = {
            "imported_count": imported_count,
            "updated_count": updated_count,
            "skipped_count": 0,
            "deleted_count": deleted_count,
        }
        db.commit()
        return {
            **self.get_library_status(db),
            "batch_id": batch.id,
            "source_file_hash": source_file_hash,
            "imported_count": imported_count,
            "updated_count": updated_count,
            "skipped_count": 0,
            "deleted_count": deleted_count,
            "duplicate": False,
            "duplicate_of_id": batch.duplicate_of_id,
            "status": batch.status,
        }

    def list_items(self, db: Session, keyword: str | None = None) -> dict:
        items = self._query_items(db, keyword).all()
        return {
            **self.get_library_status(db),
            "keyword": keyword,
            "items": items,
        }

    def list_items_page(self, db: Session, *, keyword: str | None = None, page: int = 1, page_size: int = 20) -> tuple[dict, int]:
        query = self._query_items(db, keyword)
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return (
            {
                **self.get_library_status(db),
                "keyword": keyword,
                "items": items,
            },
            total,
        )

    def get_item(self, db: Session, guidance_id: str) -> GuidanceItem:
        item = db.get(GuidanceItem, guidance_id)
        if not item:
            raise NotFoundException("GUIDANCE_ITEM_NOT_FOUND", "指导书章节不存在")
        return item

    def update_item(self, db: Session, guidance_id: str, **payload) -> GuidanceItem:
        item = self.get_item(db, guidance_id)
        updates = {key: value for key, value in payload.items() if value is not None}
        if not updates:
            raise BadRequestException("GUIDANCE_ITEM_UPDATE_EMPTY", "请至少提供一个需要更新的字段")
        if "guidance_code" in updates:
            normalized_code = updates["guidance_code"].strip()
            duplicate = (
                db.query(GuidanceItem)
                .filter(GuidanceItem.guidance_code == normalized_code, GuidanceItem.id != guidance_id)
                .first()
            )
            if duplicate:
                raise ConflictException("GUIDANCE_CODE_CONFLICT", "指导书章节编码已存在")
            updates["guidance_code"] = normalized_code
        for field_name, value in updates.items():
            setattr(item, field_name, value.strip() if isinstance(value, str) else value)
        db.commit()
        db.refresh(item)
        return item

    def delete_item(self, db: Session, guidance_id: str, *, force: bool = False) -> dict:
        item = self.get_item(db, guidance_id)
        template_link_count = db.query(func.count(TemplateGuidebookLink.id)).filter(TemplateGuidebookLink.guidance_item_id == item.id).scalar() or 0
        if template_link_count and not force:
            raise ConflictException(
                "GUIDANCE_ITEM_IN_USE",
                "指导书章节已被模板项关联，无法直接删除",
                details={"linked_template_count": template_link_count},
            )
        history_link_count = db.query(func.count(GuidanceHistoryLink.id)).filter(GuidanceHistoryLink.guidance_item_id == item.id).scalar() or 0
        matched_evidence_count = db.query(func.count(Evidence.id)).filter(Evidence.matched_guidance_id == item.id).scalar() or 0
        if force and template_link_count:
            db.query(TemplateGuidebookLink).filter(TemplateGuidebookLink.guidance_item_id == item.id).delete(synchronize_session=False)
        db.delete(item)
        db.commit()
        return {
            "id": item.id,
            "linked_template_count": template_link_count,
            "linked_history_count": history_link_count,
            "matched_evidence_count": matched_evidence_count,
            "forced": force,
        }

    def search_items(self, db: Session, keyword: str) -> list[GuidanceItem]:
        normalized = keyword.strip()
        if not normalized:
            raise BadRequestException("GUIDANCE_KEYWORD_REQUIRED", "请输入搜索关键词")
        return self._query_items(db, normalized).all()

    def _find_latest_batch(self, db: Session) -> KnowledgeImportBatch | None:
        return (
            db.query(KnowledgeImportBatch)
            .filter(
                KnowledgeImportBatch.library_type == self.LIBRARY_TYPE,
                KnowledgeImportBatch.source_file == self.source_file,
            )
            .order_by(KnowledgeImportBatch.created_at.desc())
            .first()
        )

    def _build_source_file_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _query_items(self, db: Session, keyword: str | None = None):
        query = db.query(GuidanceItem)
        normalized = keyword.strip().lower() if keyword else None
        if normalized:
            pattern = f"%{normalized}%"
            query = query.filter(
                or_(
                    func.lower(func.coalesce(GuidanceItem.guidance_code, "")).like(pattern),
                    func.lower(func.coalesce(GuidanceItem.section_path, "")).like(pattern),
                    func.lower(func.coalesce(GuidanceItem.section_title, "")).like(pattern),
                    func.lower(func.coalesce(GuidanceItem.level1, "")).like(pattern),
                    func.lower(func.coalesce(GuidanceItem.level2, "")).like(pattern),
                    func.lower(func.coalesce(GuidanceItem.level3, "")).like(pattern),
                    func.lower(func.coalesce(GuidanceItem.plain_text, "")).like(pattern),
                    func.lower(func.coalesce(GuidanceItem.record_suggestion, "")).like(pattern),
                    func.lower(func.coalesce(cast(GuidanceItem.keywords_json, String), "")).like(pattern),
                    func.lower(func.coalesce(cast(GuidanceItem.check_points_json, String), "")).like(pattern),
                    func.lower(func.coalesce(cast(GuidanceItem.evidence_requirements_json, String), "")).like(pattern),
                )
            )
        return query.order_by(GuidanceItem.section_path.asc(), GuidanceItem.created_at.asc())

    def _count_items(self, db: Session) -> int:
        return db.query(func.count(GuidanceItem.id)).scalar() or 0

    def _read_file_state(self, raise_on_error: bool = False) -> dict:
        if not self.guidance_path.exists():
            if raise_on_error:
                raise NotFoundException("GUIDANCE_MD_NOT_FOUND", "指导书文件不存在，请确认 md/指导书.md 已就位")
            return {"file_exists": False, "file_empty": False, "message": "指导书文件不存在，请确认 md/指导书.md 已就位"}

        content = self.guidance_path.read_text(encoding="utf-8")
        if not content.strip():
            return {"file_exists": True, "file_empty": True, "message": "指导书.md 当前为空，请先补充内容"}

        return {"file_exists": True, "file_empty": False, "message": "指导书文件已就绪"}
