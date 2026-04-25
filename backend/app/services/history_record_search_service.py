from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.history_record import HistoryRecord
from app.repositories.history_record_repository import HistoryRecordRepository


class HistoryRecordSearchService:
    PHRASES = ("经现场核查", "查看", "未提供", "当前", "已配置", "不适用")

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

    def get_record(self, db: Session, record_id: str) -> HistoryRecord:
        record = self.repository.get(db, record_id)
        if not record:
            raise NotFoundException("HISTORY_RECORD_NOT_FOUND", "历史测评记录不存在")
        return record

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

    def _clean(self, value: str | None) -> str | None:
        normalized = value.strip() if value else None
        return normalized or None
