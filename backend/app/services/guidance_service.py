from __future__ import annotations

import hashlib
from collections import defaultdict
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

    def summary(self, db: Session) -> dict:
        return {
            "total": self._count_items(db),
            "source_file_count": self._count_distinct_source_files(db),
            "duplicate_group_count": self._count_duplicate_groups(db),
            "duplicate_item_count": self._count_duplicate_items(db),
            "level1_counts": self._group_to_dict(self._group_by_level(db, "level1"), fallback="未分类"),
            "level2_counts": self._group_to_dict(self._group_by_level(db, "level2"), fallback="未分类"),
        }

    def list_duplicate_groups(self, db: Session, *, keyword: str | None = None) -> list[dict]:
        rows = self._find_duplicate_groups(db, keyword=keyword)
        result: list[dict] = []
        for fingerprint, duplicate_count, source_file_count, section_title, section_path, level1, level2, record_suggestion in rows:
            items = self._list_items_by_duplicate_fingerprint(db, fingerprint, keyword=keyword)
            result.append(
                {
                    "fingerprint": fingerprint,
                    "duplicate_count": duplicate_count,
                    "source_file_count": source_file_count,
                    "section_title": section_title,
                    "section_path": section_path,
                    "level1": level1,
                    "level2": level2,
                    "record_suggestion": record_suggestion,
                    "items": items,
                }
            )
        return result

    def delete_duplicate_groups(self, db: Session, *, strategy: str = "keep_first", force: bool = False) -> dict:
        normalized_strategy = (strategy or "keep_first").strip().lower()
        if normalized_strategy != "keep_first":
            raise BadRequestException("GUIDANCE_DUPLICATE_STRATEGY_INVALID", "指导书重复记录删除策略仅支持 keep_first")
        groups = self.list_duplicate_groups(db)
        if not groups:
            return {
                "strategy": normalized_strategy,
                "duplicate_group_count": 0,
                "deleted_count": 0,
                "linked_template_count": 0,
                "linked_history_count": 0,
                "matched_evidence_count": 0,
                "forced": force,
            }
        delete_ids: list[str] = []
        for group in groups:
            group_items = group["items"]
            if len(group_items) <= 1:
                continue
            delete_ids.extend(item.id for item in group_items[1:])
        template_link_count, history_link_count, matched_evidence_count = self._count_links(db, delete_ids)
        if (template_link_count or history_link_count or matched_evidence_count) and not force:
            raise ConflictException(
                "GUIDANCE_ITEM_IN_USE",
                "重复指导书章节中存在被知识库引用的数据，无法直接删除",
                details={
                    "linked_template_count": template_link_count,
                    "linked_history_count": history_link_count,
                    "matched_evidence_count": matched_evidence_count,
                    "item_count": len(delete_ids),
                    "duplicate_group_count": len(groups),
                },
            )
        if force:
            self._delete_links(db, delete_ids)
        deleted_count = 0
        for guidance_id in delete_ids:
            db.delete(self.get_item(db, guidance_id))
            deleted_count += 1
        db.commit()
        return {
            "strategy": normalized_strategy,
            "duplicate_group_count": len(groups),
            "deleted_count": deleted_count,
            "linked_template_count": template_link_count,
            "linked_history_count": history_link_count,
            "matched_evidence_count": matched_evidence_count,
            "forced": force,
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

    def _count_distinct_source_files(self, db: Session) -> int:
        return db.query(func.count(func.distinct(GuidanceItem.source_file))).scalar() or 0

    def _group_by_level(self, db: Session, field_name: str) -> list[tuple[str | None, int]]:
        column = getattr(GuidanceItem, field_name)
        return db.query(column, func.count(GuidanceItem.id)).group_by(column).all()

    def _duplicate_fingerprint(self):
        normalized_plain_text = func.trim(
            func.replace(
                func.coalesce(GuidanceItem.plain_text, ""),
                func.coalesce(GuidanceItem.section_title, ""),
                "",
            )
        )
        return func.lower(
            normalized_plain_text
            + "|"
            + func.coalesce(GuidanceItem.record_suggestion, "")
        )

    def _find_duplicate_groups(self, db: Session, *, keyword: str | None = None):
        fingerprint = self._duplicate_fingerprint()
        query = self._query_items(db, keyword)
        return (
            query.with_entities(
                fingerprint.label("fingerprint"),
                func.count(GuidanceItem.id).label("duplicate_count"),
                func.count(func.distinct(GuidanceItem.source_file)).label("source_file_count"),
                func.min(GuidanceItem.section_title).label("section_title"),
                func.min(GuidanceItem.section_path).label("section_path"),
                func.min(GuidanceItem.level1).label("level1"),
                func.min(GuidanceItem.level2).label("level2"),
                func.min(GuidanceItem.record_suggestion).label("record_suggestion"),
            )
            .group_by(fingerprint)
            .having(func.count(GuidanceItem.id) > 1)
            .order_by(func.count(GuidanceItem.id).desc(), func.min(GuidanceItem.created_at).desc())
            .all()
        )

    def _list_items_by_duplicate_fingerprint(self, db: Session, fingerprint_value: str, *, keyword: str | None = None) -> list[GuidanceItem]:
        fingerprint = self._duplicate_fingerprint()
        return (
            self._query_items(db, keyword)
            .filter(fingerprint == fingerprint_value)
            .order_by(GuidanceItem.created_at.asc(), GuidanceItem.id.asc())
            .all()
        )

    def _count_duplicate_groups(self, db: Session) -> int:
        fingerprint = self._duplicate_fingerprint()
        rows = db.query(fingerprint).group_by(fingerprint).having(func.count(GuidanceItem.id) > 1).all()
        return len(rows)

    def _count_duplicate_items(self, db: Session) -> int:
        fingerprint = self._duplicate_fingerprint()
        rows = db.query(func.count(GuidanceItem.id)).group_by(fingerprint).having(func.count(GuidanceItem.id) > 1).all()
        return sum(total for (total,) in rows)

    def _count_links(self, db: Session, guidance_ids: list[str]) -> tuple[int, int, int]:
        if not guidance_ids:
            return 0, 0, 0
        template_link_count = db.query(func.count(TemplateGuidebookLink.id)).filter(TemplateGuidebookLink.guidance_item_id.in_(guidance_ids)).scalar() or 0
        history_link_count = db.query(func.count(GuidanceHistoryLink.id)).filter(GuidanceHistoryLink.guidance_item_id.in_(guidance_ids)).scalar() or 0
        matched_evidence_count = db.query(func.count(Evidence.id)).filter(Evidence.matched_guidance_id.in_(guidance_ids)).scalar() or 0
        return template_link_count, history_link_count, matched_evidence_count

    def _delete_links(self, db: Session, guidance_ids: list[str]) -> None:
        if not guidance_ids:
            return
        db.query(TemplateGuidebookLink).filter(TemplateGuidebookLink.guidance_item_id.in_(guidance_ids)).delete(synchronize_session=False)
        db.query(GuidanceHistoryLink).filter(GuidanceHistoryLink.guidance_item_id.in_(guidance_ids)).delete(synchronize_session=False)
        db.query(Evidence).filter(Evidence.matched_guidance_id.in_(guidance_ids)).update({Evidence.matched_guidance_id: None}, synchronize_session=False)

    def _group_to_dict(self, rows: list[tuple[str | None, int]], fallback: str) -> dict[str, int]:
        result: dict[str, int] = {}
        for key, total in rows:
            result[key or fallback] = total
        return result

    def _read_file_state(self, raise_on_error: bool = False) -> dict:
        if not self.guidance_path.exists():
            if raise_on_error:
                raise NotFoundException("GUIDANCE_MD_NOT_FOUND", "指导书文件不存在，请确认 md/指导书.md 已就位")
            return {"file_exists": False, "file_empty": False, "message": "指导书文件不存在，请确认 md/指导书.md 已就位"}

        content = self.guidance_path.read_text(encoding="utf-8")
        if not content.strip():
            return {"file_exists": True, "file_empty": True, "message": "指导书.md 当前为空，请先补充内容"}

        return {"file_exists": True, "file_empty": False, "message": "指导书文件已就绪"}
