from __future__ import annotations

import re
from collections import Counter
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.assessment_template import AssessmentTemplateItem, TemplateHistoryLink
from app.models.history_record import HistoryRecord
from app.repositories.history_record_repository import HistoryRecordRepository
from app.repositories.template_history_link_repository import TemplateHistoryLinkRepository
from app.services.template_item_match_service import TemplateItemMatchService


class TemplateHistoryLinkService:
    TOP_N = 5
    TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_./:-]{2,}|[一-鿿]{2,}")
    STOPWORDS = {
        "进行",
        "结果",
        "记录",
        "情况",
        "控制点",
        "测评项",
        "扩展标准",
        "符合",
        "部分符合",
        "不符合",
        "不适用",
        "核查",
        "现场",
        "查看",
        "检查",
        "确认",
        "当前",
        "已经",
        "已",
        "应",
        "要求",
        "模板",
    }

    def __init__(self) -> None:
        self.history_repository = HistoryRecordRepository()
        self.repository = TemplateHistoryLinkRepository()
        self.template_match_service = TemplateItemMatchService()

    def link_history(self, db: Session, template_item_id: str) -> dict:
        template_item = self._get_template_item(db, template_item_id)
        history_records = self.history_repository.list_all(db)
        if not history_records:
            raise BadRequestException("HISTORY_RECORD_LIBRARY_EMPTY", "历史人工记录库为空，请先导入历史记录")

        matches = self._build_matches(template_item, history_records)
        links = [
            TemplateHistoryLink(
                template_item_id=template_item.id,
                history_record_id=match["history_record"].id,
                match_score=match["match_score"],
                match_reason=match["match_reason"],
            )
            for match in matches
        ]
        self.repository.replace_for_template_item(db, template_item.id, links)
        db.commit()
        return {
            "template_item_id": template_item.id,
            "linked_count": len(links),
            "updated_count": len(links),
            "top_score": links[0].match_score if links else None,
        }

    def list_history_links(
        self,
        db: Session,
        template_item_id: str,
        compliance_result: str | None = None,
    ) -> list[dict]:
        self._get_template_item(db, template_item_id)
        normalized_result = compliance_result.strip() if compliance_result else None
        rows = self.repository.list_history_by_template_item(db, template_item_id, normalized_result)
        return [self._serialize_link(link, record) for link, record in rows]

    def _build_matches(self, template_item: AssessmentTemplateItem, history_records: list[HistoryRecord]) -> list[dict]:
        results: list[dict] = []
        for record in history_records:
            match = self._score_history_record(template_item, record)
            if match is None:
                continue
            results.append(match)
        return sorted(
            results,
            key=lambda item: (-item["match_score"], item["history_record"].sheet_name, item["history_record"].row_index),
        )[: self.TOP_N]

    def _score_history_record(self, template_item: AssessmentTemplateItem, record: HistoryRecord) -> dict | None:
        score = 0.0
        summary: list[str] = []

        template_asset_type = self.template_match_service._infer_template_asset_type(template_item)
        if template_asset_type and record.asset_type and template_asset_type == record.asset_type:
            score += 0.25
            summary.append("对象类型命中历史资产类型")

        control_point_hits = self._collect_hits(template_item.control_point or "", [record.control_point])
        if control_point_hits:
            score += 0.3
            summary.append("控制点命中历史记录")
        else:
            partial_control_hits = self._collect_hits(" ".join(self._extract_tokens(template_item.control_point or "")), self._extract_tokens(record.control_point or ""))
            if partial_control_hits:
                score += min(0.2, 0.08 + len(partial_control_hits) * 0.04)
                summary.append(f"控制点关键词重合 {len(partial_control_hits)} 个")
                control_point_hits = partial_control_hits

        item_text_hits = self._collect_hits(template_item.item_text or "", [record.item_text, record.evaluation_item])
        if item_text_hits:
            score += 0.2
            summary.append("测评项命中历史记录")
        else:
            partial_item_hits = self._collect_hits(
                " ".join(self._extract_tokens(template_item.item_text or "")),
                self._extract_tokens(record.item_text or "", record.evaluation_item or ""),
            )
            if partial_item_hits:
                score += min(0.16, 0.08 + len(partial_item_hits) * 0.03)
                summary.append(f"测评项关键词重合 {len(partial_item_hits)} 个")
                item_text_hits = partial_item_hits

        record_similarity = self._record_similarity(template_item.record_template or "", record.record_text or "")
        if record_similarity >= 0.35:
            similarity_score = min(0.2, round(record_similarity * 0.2, 2))
            score += similarity_score
            summary.append(f"结果记录写法相似度 {record_similarity:.2f}")

        template_compliance = self._normalize_compliance_result(template_item.default_compliance_result)
        history_compliance = self._normalize_compliance_result(record.compliance_result or record.compliance_status)
        if template_compliance and history_compliance and template_compliance == history_compliance:
            score += 0.05
            summary.append("符合情况一致")

        if score <= 0:
            return None

        return {
            "history_record": record,
            "match_score": round(min(score, 0.99), 2),
            "match_reason": {
                "summary": summary,
                "template_item_id": template_item.id,
                "history_record_id": record.id,
                "template_object_type": template_item.object_type,
                "template_object_category": template_item.object_category,
                "history_asset_type": record.asset_type,
                "control_point_hits": control_point_hits[:8],
                "item_text_hits": item_text_hits[:8],
                "record_similarity": round(record_similarity, 2),
                "template_compliance_result": template_item.default_compliance_result,
                "history_compliance_result": record.compliance_result or record.compliance_status,
            },
        }

    def _serialize_link(self, link: TemplateHistoryLink, record: HistoryRecord) -> dict:
        return {
            "template_item_id": link.template_item_id,
            "history_record_id": record.id,
            "match_score": link.match_score,
            "match_reason": link.match_reason,
            "history_record": record,
            "sheet_name": record.sheet_name,
            "asset_name": record.asset_name,
            "asset_type": record.asset_type,
            "asset_ip": record.asset_ip,
            "asset_version": record.asset_version,
            "control_point": record.control_point,
            "item_text": record.item_text,
            "evaluation_item": record.evaluation_item,
            "record_text": record.record_text,
            "raw_text": record.raw_text,
            "compliance_result": record.compliance_result,
            "compliance_status": record.compliance_status,
        }

    def _get_template_item(self, db: Session, template_item_id: str) -> AssessmentTemplateItem:
        item = db.get(AssessmentTemplateItem, template_item_id)
        if not item:
            raise NotFoundException("ASSESSMENT_TEMPLATE_ITEM_NOT_FOUND", "测评记录模板项不存在")
        return item

    def _record_similarity(self, left: str, right: str) -> float:
        normalized_left = self._normalize(left)
        normalized_right = self._normalize(right)
        if len(normalized_left) < 2 or len(normalized_right) < 2:
            return 0.0
        return SequenceMatcher(None, normalized_left, normalized_right).ratio()

    def _normalize_compliance_result(self, value: str | None) -> str | None:
        normalized = self._clean(value)
        return normalized or None

    def _extract_tokens(self, *parts: str) -> list[str]:
        counter: Counter[str] = Counter()
        for token in self.TOKEN_PATTERN.findall(" ".join(parts)):
            normalized = self._normalize(token)
            if len(normalized) < 2 or normalized in self.STOPWORDS:
                continue
            counter[str(token).strip()] += 1
        return [token for token, _ in counter.most_common(12)]

    def _collect_hits(self, source_text: str, candidates: list[str | None]) -> list[str]:
        normalized_source = self._normalize(source_text)
        if len(normalized_source) < 2:
            return []
        hits: list[str] = []
        for candidate in candidates:
            normalized_candidate = self._normalize(candidate)
            if len(normalized_candidate) < 2:
                continue
            if normalized_candidate in normalized_source or normalized_source in normalized_candidate:
                if str(candidate) not in hits:
                    hits.append(str(candidate))
        return hits

    def _normalize(self, value: str | None) -> str:
        return re.sub(r"\s+", "", (value or "").strip().lower())

    def _clean(self, value) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
