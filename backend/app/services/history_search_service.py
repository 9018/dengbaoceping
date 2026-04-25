from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.history_record import HistoryRecord
from app.repositories.history_record_repository import HistoryRecordRepository


class HistorySearchService:
    PHRASES = ("经现场核查", "查看", "未提供", "当前", "已配置", "不适用")

    def __init__(self) -> None:
        self.repository = HistoryRecordRepository()

    def list_records(
        self,
        db: Session,
        *,
        sheet_name: str | None = None,
        control_point: str | None = None,
        compliance_status: str | None = None,
        asset_type: str | None = None,
    ) -> list[HistoryRecord]:
        return self.repository.list_records(
            db,
            sheet_name=sheet_name.strip() if sheet_name else None,
            control_point=control_point.strip() if control_point else None,
            compliance_status=compliance_status.strip() if compliance_status else None,
            asset_type=asset_type.strip() if asset_type else None,
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

    def similar(self, db: Session, control_point: str, evaluation_item: str, asset_type: str | None = None) -> list[dict]:
        normalized_control_point = control_point.strip()
        normalized_evaluation_item = evaluation_item.strip()
        if not normalized_control_point or not normalized_evaluation_item:
            raise BadRequestException("HISTORY_SIMILAR_QUERY_REQUIRED", "similar 查询需要 control_point 和 evaluation_item")
        records = self.repository.list_all(db)
        keywords = self._extract_query_keywords(normalized_control_point, normalized_evaluation_item)
        results: list[dict] = []
        for record in records:
            score = 0.0
            reasons: list[str] = []
            if record.control_point and normalized_control_point in record.control_point:
                score += 4
                reasons.append("控制点命中")
            elif record.control_point and self._has_overlap(record.control_point, normalized_control_point):
                score += 2
                reasons.append("控制点部分重合")
            if record.evaluation_item and normalized_evaluation_item in record.evaluation_item:
                score += 4
                reasons.append("测评项命中")
            elif record.evaluation_item and self._has_overlap(record.evaluation_item, normalized_evaluation_item):
                score += 2
                reasons.append("测评项部分重合")
            overlap = len(set(record.keywords_json or []).intersection(keywords))
            if overlap:
                score += overlap
                reasons.append(f"关键词重合 {overlap} 个")
            if asset_type and record.asset_type == asset_type:
                score += 2
                reasons.append("资产类型命中")
            if score <= 0:
                continue
            results.append(
                {
                    "id": record.id,
                    "sheet_name": record.sheet_name,
                    "asset_name": record.asset_name,
                    "asset_type": record.asset_type,
                    "control_point": record.control_point,
                    "evaluation_item": record.evaluation_item,
                    "compliance_status": record.compliance_status,
                    "score": score,
                    "reasons": reasons,
                }
            )
        return sorted(results, key=lambda item: (-item["score"], item["sheet_name"], item["asset_name"]))[:10]

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

    def _group_to_dict(self, rows: list[tuple[str | None, int]], fallback: str) -> dict[str, int]:
        result: dict[str, int] = {}
        for key, total in rows:
            result[key or fallback] = total
        return result

    def _build_haystack(self, record: HistoryRecord) -> str:
        return " ".join(
            [
                record.sheet_name or "",
                record.asset_name or "",
                record.asset_type or "",
                record.control_point or "",
                record.evaluation_item or "",
                record.record_text or "",
                record.item_no or "",
                " ".join(record.keywords_json or []),
            ]
        ).lower()

    def _extract_query_keywords(self, control_point: str, evaluation_item: str) -> set[str]:
        tokens = set()
        for chunk in (control_point, evaluation_item):
            for item in chunk.replace("/", " ").replace("、", " ").split():
                cleaned = item.strip().lower()
                if len(cleaned) >= 2:
                    tokens.add(cleaned)
        return tokens

    def _has_overlap(self, left: str, right: str) -> bool:
        left_tokens = {item for item in left.replace("/", " ").replace("、", " ").split() if len(item) >= 2}
        right_tokens = {item for item in right.replace("/", " ").replace("、", " ").split() if len(item) >= 2}
        return bool(left_tokens.intersection(right_tokens))
