from __future__ import annotations

import re
from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.extracted_field_repository import ExtractedFieldRepository
from app.services.guidance_history_link_service import GuidanceHistoryLinkService
from app.services.guidance_service import GuidanceService


class GuidanceMatchService:
    TOP_N = 3
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
        self.evidence_repository = EvidenceRepository()
        self.field_repository = ExtractedFieldRepository()
        self.guidance_service = GuidanceService()
        self.history_link_service = GuidanceHistoryLinkService()

    def match_guidance(self, db: Session, evidence_id: str, force: bool = False):
        evidence = self._get_evidence(db, evidence_id)
        if evidence.guidance_match_status == "confirmed" and not force:
            return evidence

        guidance_items = self.guidance_service.list_items(db).get("items") or []
        if not guidance_items:
            raise BadRequestException("GUIDANCE_LIBRARY_EMPTY", "指导书库为空，请先导入指导书")

        extracted_fields = self.field_repository.list_by_evidence(db, evidence.id)
        signals = self._build_signals(evidence, extracted_fields)
        if not signals["full_text"] and not signals["field_values"]:
            raise BadRequestException("EVIDENCE_GUIDANCE_MATCH_INPUT_NOT_FOUND", "证据缺少可用于匹配指导书的 OCR 文本或抽取字段")

        candidates = [self._score_guidance_item(item, signals) for item in guidance_items]
        candidates = [candidate for candidate in candidates if candidate["score"] > 0]
        candidates.sort(key=lambda item: item["score"], reverse=True)
        best_match = candidates[0] if candidates else None

        if best_match:
            links = self.history_link_service._build_matches(best_match["item"], self.history_link_service.history_repository.list_all(db))
            evidence.matched_guidance_id = best_match["item"].id
            evidence.guidance_match_score = best_match["score"]
            evidence.guidance_match_reasons_json = {
                "summary": best_match["summary"],
                "matched_guidance_id": best_match["item"].id,
                "guidance_code": best_match["item"].guidance_code,
                "section_title": best_match["item"].section_title,
                "section_path": best_match["item"].section_path,
                "score": best_match["score"],
                "score_breakdown": best_match["score_breakdown"],
                "signals": signals["signal_snapshot"],
                "history_count": len(links),
                "top_history": [
                    {
                        "history_record_id": match["record"].id,
                        "sheet_name": match["record"].sheet_name,
                        "asset_name": match["record"].asset_name,
                        "asset_type": match["record"].asset_type,
                        "compliance_status": match["record"].compliance_status,
                        "match_score": match["match_score"],
                        "match_reason": match["match_reason"],
                    }
                    for match in links[: self.TOP_N]
                ],
            }
            evidence.guidance_match_status = "suggested"
        else:
            evidence.matched_guidance_id = None
            evidence.guidance_match_score = None
            evidence.guidance_match_reasons_json = {
                "summary": ["未找到可确认的指导书条目候选"],
                "signals": signals["signal_snapshot"],
                "top_history": [],
                "history_count": 0,
            }
            evidence.guidance_match_status = "unmatched"
        self.evidence_repository.update(db, evidence)
        return self._get_evidence(db, evidence_id)

    def confirm_guidance(self, db: Session, evidence_id: str, guidance_id: str | None = None):
        evidence = self._get_evidence(db, evidence_id)
        target_guidance_id = guidance_id or evidence.matched_guidance_id
        if not target_guidance_id:
            raise BadRequestException("GUIDANCE_MATCH_NOT_FOUND", "当前证据没有可确认的指导书条目")

        guidance_item = self.guidance_service.get_item(db, target_guidance_id)
        evidence.matched_guidance_id = guidance_item.id
        evidence.guidance_match_status = "confirmed"
        reasons = dict(evidence.guidance_match_reasons_json) if isinstance(evidence.guidance_match_reasons_json, dict) else {}
        reasons.update(
            {
                "confirmed_guidance_id": guidance_item.id,
                "confirmed_guidance_code": guidance_item.guidance_code,
                "confirmed_section_title": guidance_item.section_title,
            }
        )
        evidence.guidance_match_reasons_json = reasons
        self.evidence_repository.update(db, evidence)
        return self._get_evidence(db, evidence_id)

    def _get_evidence(self, db: Session, evidence_id: str):
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")
        return evidence

    def _build_signals(self, evidence, extracted_fields) -> dict[str, Any]:
        full_text = evidence.text_content or ""
        ocr_result = evidence.ocr_result_json if isinstance(evidence.ocr_result_json, dict) else {}
        line_texts = [item.get("text", "") for item in (ocr_result.get("lines") or []) if isinstance(item, dict)]
        signal_text = "\n".join(part for part in [full_text, *line_texts] if part)

        field_values: dict[str, str] = {}
        for field in extracted_fields:
            key = (field.rule_id or field.field_name or "").strip()
            value = (field.corrected_value or field.raw_value or "").strip()
            if key and value:
                field_values[key] = value

        best_name = field_values.get("device_name") or field_values.get("hostname") or evidence.device
        best_ip = field_values.get("device_ip") or field_values.get("management_ip")
        asset_type = self._infer_asset_type(signal_text, best_name)
        tokens = self._extract_tokens(signal_text, best_name, best_ip, *field_values.values())

        return {
            "full_text": signal_text,
            "field_values": field_values,
            "best_name": best_name,
            "best_ip": best_ip,
            "asset_type": asset_type,
            "tokens": tokens,
            "signal_snapshot": {
                "device_name": best_name,
                "device_ip": best_ip,
                "asset_type": asset_type,
                "field_values": field_values,
                "tokens": tokens,
            },
        }

    def _score_guidance_item(self, item, signals: dict[str, Any]) -> dict[str, Any]:
        score = 0.0
        summary: list[str] = []
        score_breakdown: dict[str, float] = {}

        guidance_asset_type = self._infer_guidance_asset_type(item)
        if guidance_asset_type and signals["asset_type"] and guidance_asset_type == signals["asset_type"]:
            score += 2.0
            score_breakdown["asset_type_hit"] = 2.0
            summary.append("资产类型命中")

        content_text = " ".join(
            [
                item.section_title or "",
                item.section_path or "",
                item.plain_text or "",
                item.record_suggestion or "",
                " ".join(item.keywords_json or []),
                " ".join(item.check_points_json or []),
                " ".join(item.evidence_requirements_json or []),
            ]
        )
        normalized_content = self._normalize(content_text)

        text_hits = self._collect_hits(content_text, [signals["best_name"], signals["best_ip"]])
        if text_hits:
            hit_score = min(3.0, 1.5 + 0.8 * len(text_hits))
            score += hit_score
            score_breakdown["signal_text_hits"] = round(hit_score, 2)
            summary.append("证据关键信号命中指导书")

        checkpoint_hits = self._collect_hits(signals["full_text"], list(item.check_points_json or []))
        if checkpoint_hits:
            hit_score = min(4.0, 1.5 + 0.7 * len(checkpoint_hits))
            score += hit_score
            score_breakdown["checkpoint_hits"] = round(hit_score, 2)
            summary.append("核查要点命中")

        evidence_hits = self._collect_hits(signals["full_text"], list(item.evidence_requirements_json or []))
        if evidence_hits:
            hit_score = min(3.0, 1.0 + 0.6 * len(evidence_hits))
            score += hit_score
            score_breakdown["evidence_requirement_hits"] = round(hit_score, 2)
            summary.append("证据要求命中")

        keyword_overlap = [token for token in signals["tokens"] if token in normalized_content]
        if keyword_overlap:
            overlap_score = min(3.0, float(len(keyword_overlap)) * 0.5)
            score += overlap_score
            score_breakdown["keyword_overlap"] = round(overlap_score, 2)
            summary.append(f"关键词重合 {len(keyword_overlap)} 个")

        return {
            "item": item,
            "score": round(score, 2),
            "summary": summary,
            "score_breakdown": {
                **score_breakdown,
                "guidance_asset_type": guidance_asset_type,
                "checkpoint_hits": checkpoint_hits[:8],
                "evidence_requirement_hits": evidence_hits[:8],
                "signal_text_hits": text_hits[:8],
                "keyword_overlap_tokens": keyword_overlap[:8],
            },
        }

    def _infer_asset_type(self, text: str, best_name: str | None) -> str | None:
        normalized = f"{text} {(best_name or '').lower()}"
        for keyword, asset_type in self.ASSET_TYPE_RULES:
            if keyword.lower() in normalized.lower():
                return asset_type
        lowered = (best_name or "").lower()
        if lowered.startswith("fw"):
            return "firewall"
        if lowered.startswith("sw") or lowered.startswith("h3c"):
            return "switch"
        if lowered.startswith("win") or lowered.startswith("srv"):
            return "server"
        return None

    def _infer_guidance_asset_type(self, item) -> str | None:
        content = " ".join([item.section_title or "", item.section_path or "", item.plain_text or "", item.record_suggestion or ""])
        for keyword, asset_type in self.ASSET_TYPE_RULES:
            if keyword in content:
                return asset_type
        return None

    def _extract_tokens(self, *parts: str | None) -> list[str]:
        counter: Counter[str] = Counter()
        for token in self.TOKEN_PATTERN.findall(" ".join(part or "" for part in parts)):
            normalized = self._normalize(token)
            if len(normalized) < 2 or normalized in self.STOPWORDS:
                continue
            counter[normalized] += 1
        return [item for item, _ in counter.most_common(12)]

    def _collect_hits(self, source_text: str, candidates: list[str | None]) -> list[str]:
        normalized_source = self._normalize(source_text)
        hits: list[str] = []
        for candidate in candidates:
            normalized_candidate = self._normalize(candidate)
            if len(normalized_candidate) < 2:
                continue
            if normalized_candidate in normalized_source or normalized_source in normalized_candidate:
                if normalized_candidate not in hits:
                    hits.append(normalized_candidate)
        return hits

    def _normalize(self, value: str | None) -> str:
        return re.sub(r"\s+", "", (value or "").strip().lower())
