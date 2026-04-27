from __future__ import annotations

import re
from collections import Counter

from sqlalchemy.orm import Session

from app.models.guidance_history_link import GuidanceHistoryLink
from app.models.history_record import HistoryRecord
from app.repositories.guidance_history_link_repository import GuidanceHistoryLinkRepository
from app.repositories.history_record_repository import HistoryRecordRepository
from app.services.guidance_service import GuidanceService
from app.services.history_search_service import HistorySearchService


class GuidanceHistoryLinkService:
    TOP_N = 10
    TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{3,}|[一-鿿]{2,}")
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
        "应",
        "提供",
        "查看",
        "当前",
    }
    ASSET_TYPE_RULES = (
        ("防火墙", "firewall"),
        ("交换机", "switch"),
        ("服务器", "server"),
        ("数据库", "database"),
        ("安全管理", "management"),
        ("管理平台", "management"),
    )

    def __init__(self) -> None:
        self.guidance_service = GuidanceService()
        self.history_service = HistorySearchService()
        self.history_repository = HistoryRecordRepository()
        self.repository = GuidanceHistoryLinkRepository()

    def link_history(self, db: Session, guidance_id: str) -> dict:
        guidance_item = self.guidance_service.get_item(db, guidance_id)
        history_records = self.history_repository.list_all(db)
        matches = self._build_matches(guidance_item, history_records)
        links = [
            GuidanceHistoryLink(
                guidance_item_id=guidance_item.id,
                history_record_id=match["record"].id,
                match_score=match["match_score"],
                match_reason=match["match_reason"],
            )
            for match in matches
        ]
        self.repository.replace_for_guidance(db, guidance_item.id, links)
        db.commit()
        return {
            "guidance_item_id": guidance_item.id,
            "linked_count": len(links),
            "updated_count": len(links),
            "top_score": links[0].match_score if links else None,
        }

    def list_history_by_guidance(
        self,
        db: Session,
        guidance_id: str,
        compliance_status: str | None = None,
    ) -> list[dict]:
        self.guidance_service.get_item(db, guidance_id)
        normalized_status = compliance_status.strip() if compliance_status else None
        rows = self.repository.list_history_by_guidance(db, guidance_id, normalized_status)
        return [self._build_history_link_payload(link, record) for link, record in rows]

    def list_history_by_guidance_page(
        self,
        db: Session,
        guidance_id: str,
        compliance_status: str | None = None,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        self.guidance_service.get_item(db, guidance_id)
        normalized_status = compliance_status.strip() if compliance_status else None
        rows, total = self.repository.list_history_by_guidance_page(
            db,
            guidance_id,
            normalized_status,
            page=page,
            page_size=page_size,
        )
        return [self._build_history_link_payload(link, record) for link, record in rows], total

    def list_guidance_by_history(self, db: Session, history_id: str) -> list[dict]:
        self.history_service.get_record(db, history_id)
        rows = self.repository.list_guidance_by_history(db, history_id)
        return [
            {
                "history_record_id": history_id,
                "guidance_item_id": item.id,
                "match_score": link.match_score,
                "match_reason": link.match_reason,
                "section_title": item.section_title,
                "section_path": item.section_path,
                "guidance_code": item.guidance_code,
            }
            for link, item in rows
        ]

    def _build_history_link_payload(self, link: GuidanceHistoryLink, record: HistoryRecord) -> dict:
        return {
            "guidance_item_id": link.guidance_item_id,
            "history_record_id": record.id,
            "match_score": link.match_score,
            "match_reason": link.match_reason,
            "record_text": record.record_text,
            "compliance_status": record.compliance_status,
            "asset_type": record.asset_type,
            "control_point": record.control_point,
            "evaluation_item": record.evaluation_item,
            "sheet_name": record.sheet_name,
        }

    def _build_matches(self, guidance_item, history_records: list[HistoryRecord]) -> list[dict]:
        guidance_asset_type = self._infer_asset_type(guidance_item)
        guidance_keywords = self._build_guidance_keywords(guidance_item)
        guidance_control_text = " ".join(
            [
                guidance_item.section_title or "",
                guidance_item.section_path or "",
                " ".join(guidance_item.check_points_json or []),
                guidance_item.plain_text or "",
            ]
        )
        guidance_eval_text = " ".join(
            [
                guidance_item.record_suggestion or "",
                " ".join(guidance_item.evidence_requirements_json or []),
                guidance_item.plain_text or "",
            ]
        )
        results: list[dict] = []
        for record in history_records:
            match = self._score_record(
                guidance_control_text=guidance_control_text,
                guidance_eval_text=guidance_eval_text,
                guidance_asset_type=guidance_asset_type,
                guidance_keywords=guidance_keywords,
                record=record,
            )
            if match is None:
                continue
            results.append(match)
        return sorted(
            results,
            key=lambda item: (-item["match_score"], item["record"].sheet_name, item["record"].row_index),
        )[: self.TOP_N]

    def _score_record(
        self,
        *,
        guidance_control_text: str,
        guidance_eval_text: str,
        guidance_asset_type: str | None,
        guidance_keywords: list[str],
        record: HistoryRecord,
    ) -> dict | None:
        score = 0.0
        summary: list[str] = []

        control_point_hits = self._collect_hits(guidance_control_text, [record.control_point])
        if control_point_hits:
            score += 4
            summary.append("控制点命中")
        else:
            control_point_hits = self._collect_hits(guidance_control_text, self._extract_tokens(record.control_point))
            if control_point_hits:
                score += min(3.0, 1.0 + len(control_point_hits) * 0.5)
                summary.append("控制点部分重合")

        evaluation_text_hits = self._collect_hits(guidance_eval_text, [record.evaluation_item, record.record_text])
        if evaluation_text_hits:
            score += 4
            summary.append("测评项/结果记录命中")
        else:
            evaluation_text_hits = self._collect_hits(
                guidance_eval_text,
                self._extract_tokens(record.evaluation_item, record.record_text),
            )
            if evaluation_text_hits:
                score += min(3.0, 1.0 + len(evaluation_text_hits) * 0.4)
                summary.append("测评项/结果记录部分重合")

        keyword_overlap = self._collect_hits(" ".join([guidance_control_text, guidance_eval_text]), guidance_keywords + list(record.keywords_json or []))
        if keyword_overlap:
            score += min(3.0, float(len(keyword_overlap)))
            summary.append(f"关键词重合 {len(keyword_overlap)} 个")

        if guidance_asset_type and record.asset_type == guidance_asset_type:
            score += 2
            summary.append("资产类型命中")

        if score <= 0:
            return None

        return {
            "record": record,
            "match_score": round(score, 2),
            "match_reason": {
                "summary": summary,
                "guidance_asset_type": guidance_asset_type,
                "history_asset_type": record.asset_type,
                "keyword_overlap": keyword_overlap[:8],
                "control_point_hits": control_point_hits[:8],
                "evaluation_text_hits": evaluation_text_hits[:8],
            },
        }

    def _build_guidance_keywords(self, guidance_item) -> list[str]:
        return list(
            dict.fromkeys(
                [
                    *(guidance_item.keywords_json or []),
                    *(guidance_item.check_points_json or []),
                    *(guidance_item.evidence_requirements_json or []),
                    *(self._extract_tokens(guidance_item.section_title, guidance_item.section_path, guidance_item.plain_text)),
                ]
            )
        )

    def _infer_asset_type(self, guidance_item) -> str | None:
        content = " ".join(
            [
                guidance_item.section_title or "",
                guidance_item.section_path or "",
                guidance_item.plain_text or "",
                guidance_item.record_suggestion or "",
            ]
        )
        for keyword, asset_type in self.ASSET_TYPE_RULES:
            if keyword in content:
                return asset_type
        return None

    def _extract_tokens(self, *parts: str | None) -> list[str]:
        counter: Counter[str] = Counter()
        for token in self.TOKEN_PATTERN.findall(" ".join(part or "" for part in parts)):
            normalized = token.strip().lower()
            if len(normalized) < 2 or normalized in self.STOPWORDS:
                continue
            counter[normalized] += 1
        return [item for item, _ in counter.most_common(12)]

    def _collect_hits(self, source_text: str, candidates: list[str | None]) -> list[str]:
        normalized_source = self._normalize_text(source_text)
        hits: list[str] = []
        for candidate in candidates:
            normalized_candidate = self._normalize_text(candidate)
            if len(normalized_candidate) < 2:
                continue
            if normalized_candidate in normalized_source or normalized_source in normalized_candidate:
                if normalized_candidate not in hits:
                    hits.append(normalized_candidate)
        return hits

    def _normalize_text(self, value: str | None) -> str:
        return re.sub(r"\s+", "", (value or "").strip().lower())
