from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.assessment_template import TemplateHistoryLink
from app.models.guidance_history_link import GuidanceHistoryLink
from app.models.history_record import HistoryRecord
from app.repositories.history_record_repository import HistoryRecordRepository


class HistoryRecordSearchService:
    PHRASES = ("经现场核查", "查看", "未提供", "当前", "已配置", "不适用")
    MANAGEABLE_FIELDS = {
        "sheet_name": "工作表",
        "asset_type": "资产类型",
        "compliance_result": "符合情况",
        "compliance_status": "符合状态",
    }

    def __init__(self) -> None:
        self.repository = HistoryRecordRepository()

    def list_records(
        self,
        db: Session,
        *,
        asset_name: str | None = None,
        asset_type: str | None = None,
        sheet_name: str | None = None,
        control_point: str | None = None,
        item_text: str | None = None,
        compliance_result: str | None = None,
        compliance_status: str | None = None,
        keyword: str | None = None,
        project_name: str | None = None,
        asset_ip: str | None = None,
        standard_type: str | None = None,
        item_code: str | None = None,
    ) -> list[HistoryRecord]:
        return self.repository.list_records(
            db,
            asset_name=self._clean(asset_name),
            asset_type=self._clean(asset_type),
            sheet_name=self._clean(sheet_name),
            control_point=self._clean(control_point),
            item_text=self._clean(item_text),
            compliance_result=self._clean(compliance_result),
            compliance_status=self._clean(compliance_status or compliance_result),
            keyword=self._clean(keyword),
            project_name=self._clean(project_name),
            asset_ip=self._clean(asset_ip),
            standard_type=self._clean(standard_type),
            item_code=self._clean(item_code),
        )

    def list_records_page(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        asset_name: str | None = None,
        asset_type: str | None = None,
        sheet_name: str | None = None,
        control_point: str | None = None,
        item_text: str | None = None,
        compliance_result: str | None = None,
        compliance_status: str | None = None,
        keyword: str | None = None,
        project_name: str | None = None,
        asset_ip: str | None = None,
        standard_type: str | None = None,
        item_code: str | None = None,
    ) -> tuple[list[HistoryRecord], int]:
        return self.repository.list_records_page(
            db,
            page=page,
            page_size=page_size,
            asset_name=self._clean(asset_name),
            asset_type=self._clean(asset_type),
            sheet_name=self._clean(sheet_name),
            control_point=self._clean(control_point),
            item_text=self._clean(item_text),
            compliance_result=self._clean(compliance_result),
            compliance_status=self._clean(compliance_status or compliance_result),
            keyword=self._clean(keyword),
            project_name=self._clean(project_name),
            asset_ip=self._clean(asset_ip),
            standard_type=self._clean(standard_type),
            item_code=self._clean(item_code),
        )

    def get_record(self, db: Session, record_id: str) -> HistoryRecord:
        record = self.repository.get(db, record_id)
        if not record:
            raise NotFoundException("HISTORY_RECORD_NOT_FOUND", "历史测评记录不存在")
        return record

    def update_record(self, db: Session, record_id: str, **payload) -> HistoryRecord:
        record = self.get_record(db, record_id)
        updates = {key: value for key, value in payload.items() if value is not None}
        if not updates:
            raise BadRequestException("HISTORY_RECORD_UPDATE_EMPTY", "请至少提供一个需要更新的字段")
        for field_name, value in updates.items():
            setattr(record, field_name, value.strip() if isinstance(value, str) else value)
        db.commit()
        db.refresh(record)
        return record

    def delete_record(self, db: Session, record_id: str, *, force: bool = False) -> dict:
        record = self.get_record(db, record_id)
        template_link_count = db.query(func.count(TemplateHistoryLink.id)).filter(TemplateHistoryLink.history_record_id == record.id).scalar() or 0
        guidance_link_count = db.query(func.count(GuidanceHistoryLink.id)).filter(GuidanceHistoryLink.history_record_id == record.id).scalar() or 0
        if (template_link_count or guidance_link_count) and not force:
            raise ConflictException(
                "HISTORY_RECORD_IN_USE",
                "历史记录已被知识库关联引用，无法直接删除",
                details={
                    "linked_template_count": template_link_count,
                    "linked_guidance_count": guidance_link_count,
                },
            )
        if force and template_link_count:
            db.query(TemplateHistoryLink).filter(TemplateHistoryLink.history_record_id == record.id).delete(synchronize_session=False)
        if force and guidance_link_count:
            db.query(GuidanceHistoryLink).filter(GuidanceHistoryLink.history_record_id == record.id).delete(synchronize_session=False)
        db.delete(record)
        db.commit()
        return {
            "id": record.id,
            "linked_template_count": template_link_count,
            "linked_guidance_count": guidance_link_count,
            "forced": force,
        }

    def delete_by_source(self, db: Session, *, source_file: str | None = None, source_file_hash: str | None = None, force: bool = False) -> dict:
        normalized_source_file = self._clean(source_file)
        normalized_source_file_hash = self._clean(source_file_hash)
        if not normalized_source_file and not normalized_source_file_hash:
            raise BadRequestException("HISTORY_SOURCE_REQUIRED", "请提供 source_file 或 source_file_hash")
        query = db.query(HistoryRecord)
        if normalized_source_file:
            query = query.filter(HistoryRecord.source_file == normalized_source_file)
        if normalized_source_file_hash:
            query = query.filter(HistoryRecord.source_file_hash == normalized_source_file_hash)
        records = query.all()
        if not records:
            raise NotFoundException("HISTORY_SOURCE_NOT_FOUND", "未找到对应来源的历史记录")
        record_ids = [item.id for item in records]
        template_link_count, guidance_link_count = self._count_links(db, record_ids)
        if (template_link_count or guidance_link_count) and not force:
            raise ConflictException(
                "HISTORY_RECORD_IN_USE",
                "该来源历史记录已被知识库关联引用，无法直接删除",
                details={
                    "linked_template_count": template_link_count,
                    "linked_guidance_count": guidance_link_count,
                    "record_count": len(record_ids),
                },
            )
        self._delete_links(db, record_ids, force=force)
        deleted_count = query.delete(synchronize_session=False)
        db.commit()
        return {
            "deleted_count": deleted_count,
            "linked_template_count": template_link_count,
            "linked_guidance_count": guidance_link_count,
            "forced": force,
        }

    def search(self, db: Session, keyword: str) -> list[HistoryRecord]:
        normalized = keyword.strip()
        if not normalized:
            raise BadRequestException("HISTORY_KEYWORD_REQUIRED", "请输入搜索关键词")
        records = self.repository.list_by_keyword(db, normalized)
        lowered = normalized.lower()
        return [record for record in records if lowered in self._build_haystack(record)]

    def stats(self, db: Session) -> dict:
        return {
            "sheet_count": self.repository.count_distinct_sheets(db),
            "total": self.repository.count(db),
            "compliance_status_counts": self._group_to_dict(self.repository.group_by_status(db), fallback="未标注"),
            "asset_type_counts": self._group_to_dict(self.repository.group_by_asset_type(db), fallback="未分类"),
        }

    def summary(self, db: Session) -> dict:
        return {
            "total": self.repository.count(db),
            "sheet_count": self.repository.count_distinct_sheets(db),
            "source_file_count": self.repository.count_distinct_source_files(db),
            "duplicate_group_count": self.repository.count_duplicate_groups(db),
            "duplicate_record_count": self.repository.count_duplicate_records(db),
            "compliance_status_counts": self._group_to_dict(self.repository.group_by_status(db), fallback="未标注"),
            "asset_type_counts": self._group_to_dict(self.repository.group_by_asset_type(db), fallback="未分类"),
        }

    def list_field_values(self, db: Session, field_name: str) -> list[dict]:
        normalized_field = self._normalize_manageable_field(field_name)
        rows = self.repository.list_distinct_field_values(db, normalized_field)
        return [
            {
                "value": (value or "").strip() or "未填写",
                "count": count,
            }
            for value, count in rows
            if (value or "").strip()
        ]

    def rename_field_value(self, db: Session, field_name: str, from_value: str, to_value: str) -> dict:
        normalized_field = self._normalize_manageable_field(field_name)
        source_value = self._required_value(from_value, "HISTORY_FIELD_VALUE_REQUIRED", "请提供待重命名的字段值")
        target_value = self._required_value(to_value, "HISTORY_FIELD_VALUE_REQUIRED", "请提供新的字段值")
        if source_value == target_value:
            raise BadRequestException("HISTORY_FIELD_VALUE_UNCHANGED", "新旧字段值不能相同")
        updated_count = self.repository.update_field_value(db, normalized_field, source_value, target_value)
        if updated_count <= 0:
            raise NotFoundException("HISTORY_FIELD_VALUE_NOT_FOUND", "未找到对应字段值的历史记录")
        db.commit()
        return {
            "field_name": normalized_field,
            "from_value": source_value,
            "to_value": target_value,
            "updated_count": updated_count,
        }

    def delete_by_field_value(self, db: Session, field_name: str, field_value: str, *, force: bool = False) -> dict:
        normalized_field = self._normalize_manageable_field(field_name)
        normalized_value = self._required_value(field_value, "HISTORY_FIELD_VALUE_REQUIRED", "请提供字段值")
        records = self.repository.list_records_by_field_value(db, normalized_field, normalized_value)
        if not records:
            raise NotFoundException("HISTORY_FIELD_VALUE_NOT_FOUND", "未找到对应字段值的历史记录")
        record_ids = [item.id for item in records]
        template_link_count, guidance_link_count = self._count_links(db, record_ids)
        if (template_link_count or guidance_link_count) and not force:
            raise ConflictException(
                "HISTORY_RECORD_IN_USE",
                "该字段值对应历史记录已被知识库关联引用，无法直接删除",
                details={
                    "field_name": normalized_field,
                    "field_value": normalized_value,
                    "linked_template_count": template_link_count,
                    "linked_guidance_count": guidance_link_count,
                    "record_count": len(record_ids),
                },
            )
        self._delete_links(db, record_ids, force=force)
        deleted_count = self.repository.delete_by_field_value(db, normalized_field, normalized_value)
        db.commit()
        return {
            "field_name": normalized_field,
            "field_value": normalized_value,
            "deleted_count": deleted_count,
            "linked_template_count": template_link_count,
            "linked_guidance_count": guidance_link_count,
            "forced": force,
        }

    def list_duplicate_groups(
        self,
        db: Session,
        *,
        asset_name: str | None = None,
        asset_type: str | None = None,
        sheet_name: str | None = None,
        control_point: str | None = None,
        item_text: str | None = None,
        compliance_result: str | None = None,
        compliance_status: str | None = None,
        keyword: str | None = None,
        project_name: str | None = None,
        asset_ip: str | None = None,
        standard_type: str | None = None,
        item_code: str | None = None,
    ) -> list[dict]:
        rows = self.repository.find_duplicate_groups(
            db,
            asset_name=self._clean(asset_name),
            asset_type=self._clean(asset_type),
            sheet_name=self._clean(sheet_name),
            control_point=self._clean(control_point),
            item_text=self._clean(item_text),
            compliance_result=self._clean(compliance_result),
            compliance_status=self._clean(compliance_status or compliance_result),
            keyword=self._clean(keyword),
            project_name=self._clean(project_name),
            asset_ip=self._clean(asset_ip),
            standard_type=self._clean(standard_type),
            item_code=self._clean(item_code),
        )
        result: list[dict] = []
        for fingerprint, duplicate_count, source_file_count, group_sheet_name, group_asset_name, group_asset_type, group_control_point, group_item_text, group_compliance_result in rows:
            records = self.repository.list_records_by_duplicate_fingerprint(
                db,
                fingerprint,
                asset_name=self._clean(asset_name),
                asset_type=self._clean(asset_type),
                sheet_name=self._clean(sheet_name),
                control_point=self._clean(control_point),
                item_text=self._clean(item_text),
                compliance_result=self._clean(compliance_result),
                compliance_status=self._clean(compliance_status or compliance_result),
                keyword=self._clean(keyword),
                project_name=self._clean(project_name),
                asset_ip=self._clean(asset_ip),
                standard_type=self._clean(standard_type),
                item_code=self._clean(item_code),
            )
            result.append(
                {
                    "fingerprint": fingerprint,
                    "duplicate_count": duplicate_count,
                    "source_file_count": source_file_count,
                    "sheet_name": group_sheet_name,
                    "asset_name": group_asset_name,
                    "asset_type": group_asset_type,
                    "control_point": group_control_point,
                    "item_text": group_item_text,
                    "compliance_result": group_compliance_result,
                    "records": records,
                }
            )
        return result

    def delete_duplicate_groups(self, db: Session, *, strategy: str = "keep_first", force: bool = False) -> dict:
        normalized_strategy = (strategy or "keep_first").strip().lower()
        if normalized_strategy != "keep_first":
            raise BadRequestException("HISTORY_DUPLICATE_STRATEGY_INVALID", "重复记录删除策略仅支持 keep_first")
        groups = self.list_duplicate_groups(db)
        if not groups:
            return {
                "strategy": normalized_strategy,
                "duplicate_group_count": 0,
                "deleted_count": 0,
                "linked_template_count": 0,
                "linked_guidance_count": 0,
                "forced": force,
            }
        delete_ids: list[str] = []
        for group in groups:
            group_records = group["records"]
            if len(group_records) <= 1:
                continue
            delete_ids.extend(record.id for record in group_records[1:])
        template_link_count, guidance_link_count = self._count_links(db, delete_ids)
        if (template_link_count or guidance_link_count) and not force:
            raise ConflictException(
                "HISTORY_RECORD_IN_USE",
                "重复历史记录中存在被知识库引用的数据，无法直接删除",
                details={
                    "linked_template_count": template_link_count,
                    "linked_guidance_count": guidance_link_count,
                    "record_count": len(delete_ids),
                    "duplicate_group_count": len(groups),
                },
            )
        self._delete_links(db, delete_ids, force=force)
        deleted_count = 0
        for record_id in delete_ids:
            db.delete(self.get_record(db, record_id))
            deleted_count += 1
        db.commit()
        return {
            "strategy": normalized_strategy,
            "duplicate_group_count": len(groups),
            "deleted_count": deleted_count,
            "linked_template_count": template_link_count,
            "linked_guidance_count": guidance_link_count,
            "forced": force,
        }

    def search_similar(
        self,
        db: Session,
        *,
        ocr_text: str | None = None,
        asset_type: str | None = None,
        page_type: str | None = None,
        control_point: str | None = None,
        item_text: str | None = None,
    ) -> list[dict]:
        if not any(self._clean(item) for item in (ocr_text, asset_type, page_type, control_point, item_text)):
            raise BadRequestException("HISTORY_SIMILAR_QUERY_REQUIRED", "请输入相似搜索条件")
        records = self.repository.list_all(db)
        query_keywords = self._extract_query_keywords(ocr_text, control_point, item_text, page_type)
        normalized_control = self._clean(control_point)
        normalized_item = self._clean(item_text)
        normalized_ocr = self._clean(ocr_text)
        normalized_page_type = self._clean(page_type)
        normalized_asset_type = self._clean(asset_type)
        results: list[dict] = []
        for record in records:
            score = 0.0
            reasons: list[str] = []
            record_item_text = record.item_text or record.evaluation_item
            record_raw_text = record.raw_text or record.record_text
            if normalized_control and record.control_point and normalized_control in record.control_point:
                score += 4
                reasons.append("控制点命中")
            elif normalized_control and record.control_point and self._has_overlap(record.control_point, normalized_control):
                score += 2
                reasons.append("控制点部分重合")
            if normalized_item and record_item_text and normalized_item in record_item_text:
                score += 4
                reasons.append("测评项命中")
            elif normalized_item and record_item_text and self._has_overlap(record_item_text, normalized_item):
                score += 2
                reasons.append("测评项部分重合")
            if normalized_ocr and record_raw_text and self._has_overlap(record_raw_text, normalized_ocr):
                score += 2
                reasons.append("OCR文本与历史记录重合")
            overlap = len(set(record.keywords_json or []).intersection(query_keywords))
            if overlap:
                score += overlap
                reasons.append(f"关键词重合 {overlap} 个")
            if normalized_asset_type and record.asset_type == normalized_asset_type:
                score += 2
                reasons.append("资产类型命中")
            if normalized_page_type and normalized_page_type in self._build_haystack(record):
                score += 1
                reasons.append("页面类型命中")
            if score <= 0:
                continue
            results.append(self._build_similar_result(record, score, reasons))
        return sorted(results, key=lambda item: (-item["score"], item["sheet_name"], item["asset_name"]))[:10]

    def similar(self, db: Session, control_point: str, evaluation_item: str, asset_type: str | None = None) -> list[dict]:
        return self.search_similar(db, control_point=control_point, item_text=evaluation_item, asset_type=asset_type)

    def phrases(self, db: Session) -> list[dict]:
        records = self.repository.list_all(db)
        result: list[dict] = []
        for phrase in self.PHRASES:
            total = 0
            grouped: dict[str, int] = defaultdict(int)
            for record in records:
                if phrase not in (record.record_text or ""):
                    continue
                total += 1
                grouped[record.compliance_status or "未标注"] += 1
            result.append({"phrase": phrase, "total": total, "compliance_status_counts": dict(grouped)})
        return result

    def _build_similar_result(self, record: HistoryRecord, score: float, reasons: list[str]) -> dict:
        return {
            "id": record.id,
            "source_file": record.source_file,
            "project_name": record.project_name,
            "sheet_name": record.sheet_name,
            "asset_name": record.asset_name,
            "asset_type": record.asset_type,
            "asset_ip": record.asset_ip,
            "asset_version": record.asset_version,
            "standard_type": record.standard_type,
            "control_point": record.control_point,
            "item_text": record.item_text or record.evaluation_item,
            "evaluation_item": record.evaluation_item,
            "record_text": record.record_text,
            "raw_text": record.raw_text,
            "compliance_result": record.compliance_result or record.compliance_status,
            "compliance_status": record.compliance_status,
            "score_weight": record.score_weight,
            "item_code": record.item_code or record.item_no,
            "score": score,
            "reasons": reasons,
        }

    def _group_to_dict(self, rows: list[tuple[str | None, int]], fallback: str) -> dict[str, int]:
        result: dict[str, int] = {}
        for key, total in rows:
            result[key or fallback] = total
        return result

    def _build_haystack(self, record: HistoryRecord) -> str:
        return " ".join(
            [
                record.source_file or "",
                record.project_name or "",
                record.sheet_name or "",
                record.asset_name or "",
                record.asset_ip or "",
                record.asset_type or "",
                record.standard_type or "",
                record.control_point or "",
                record.item_text or "",
                record.evaluation_item or "",
                record.raw_text or "",
                record.record_text or "",
                record.compliance_result or "",
                record.compliance_status or "",
                record.item_code or "",
                record.item_no or "",
                " ".join(record.keywords_json or []),
            ]
        ).lower()

    def _extract_query_keywords(self, *parts: str | None) -> set[str]:
        tokens = set()
        for chunk in parts:
            for item in (chunk or "").replace("/", " ").replace("、", " ").split():
                cleaned = item.strip().lower()
                if len(cleaned) >= 2:
                    tokens.add(cleaned)
        return tokens

    def _has_overlap(self, left: str, right: str) -> bool:
        left_tokens = {item for item in left.replace("/", " ").replace("、", " ").split() if len(item) >= 2}
        right_tokens = {item for item in right.replace("/", " ").replace("、", " ").split() if len(item) >= 2}
        return bool(left_tokens.intersection(right_tokens))

    def _count_links(self, db: Session, record_ids: list[str]) -> tuple[int, int]:
        if not record_ids:
            return 0, 0
        template_link_count = db.query(func.count(TemplateHistoryLink.id)).filter(TemplateHistoryLink.history_record_id.in_(record_ids)).scalar() or 0
        guidance_link_count = db.query(func.count(GuidanceHistoryLink.id)).filter(GuidanceHistoryLink.history_record_id.in_(record_ids)).scalar() or 0
        return template_link_count, guidance_link_count

    def _delete_links(self, db: Session, record_ids: list[str], *, force: bool) -> None:
        if not force or not record_ids:
            return
        db.query(TemplateHistoryLink).filter(TemplateHistoryLink.history_record_id.in_(record_ids)).delete(synchronize_session=False)
        db.query(GuidanceHistoryLink).filter(GuidanceHistoryLink.history_record_id.in_(record_ids)).delete(synchronize_session=False)

    def _normalize_manageable_field(self, field_name: str) -> str:
        normalized = (field_name or "").strip()
        if normalized not in self.MANAGEABLE_FIELDS:
            raise BadRequestException("HISTORY_FIELD_NOT_SUPPORTED", "仅支持管理 sheet_name、asset_type、compliance_result、compliance_status")
        return normalized

    def _required_value(self, value: str | None, code: str, message: str) -> str:
        normalized = self._clean(value)
        if not normalized:
            raise BadRequestException(code, message)
        return normalized

    def _clean(self, value: str | None) -> str | None:
        normalized = value.strip() if value else None
        return normalized or None
