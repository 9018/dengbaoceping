from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.core.exceptions import BadRequestException, NotFoundException
from app.repositories.asset_repository import AssetRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.extracted_field_repository import ExtractedFieldRepository


class AssetMatchService:
    TYPE_KEYWORDS = (
        ("防火墙", "firewall"),
        ("firewall", "firewall"),
        ("交换机", "switch"),
        ("switch", "switch"),
        ("h3c", "switch"),
        ("华为", "switch"),
        ("windows", "server"),
        ("linux", "server"),
        ("服务器", "server"),
        ("数据库", "database"),
        ("database", "database"),
    )
    TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_.:-]{2,}|[一-鿿]{2,}")
    IP_PATTERN = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
    NAME_FIELD_CODES = {"device_name", "hostname"}
    IP_FIELD_CODES = {"device_ip", "management_ip"}

    def __init__(self) -> None:
        self.asset_repository = AssetRepository()
        self.evidence_repository = EvidenceRepository()
        self.field_repository = ExtractedFieldRepository()

    def match_asset(self, db, evidence_id: str, force: bool = False):
        evidence = self._get_evidence(db, evidence_id)
        if evidence.asset_match_status == "confirmed" and not force:
            return evidence

        matchable_assets = self.asset_repository.list_matchable_by_project(db, evidence.project_id)
        extracted_fields = self.field_repository.list_by_evidence(db, evidence.id)
        signals = self._build_signals(evidence, extracted_fields)
        if not signals["full_text"] and not signals["field_values"]:
            raise BadRequestException("EVIDENCE_MATCH_INPUT_NOT_FOUND", "证据缺少可用于匹配的 OCR 文本或抽取字段")

        candidates = [self._score_asset(asset, signals) for asset in matchable_assets]
        candidates = [candidate for candidate in candidates if candidate["score"] > 0]
        candidates.sort(key=lambda item: item["score"], reverse=True)
        best_match = candidates[0] if candidates else None

        suggested_asset_type = signals["suggested_asset_type"]
        suggested_asset_name = signals["best_name"] or evidence.device or evidence.title
        if best_match:
            evidence.matched_asset_id = best_match["asset"].id
            evidence.asset_match_score = best_match["score"]
            evidence.asset_match_reasons_json = {
                "summary": best_match["summary"],
                "matched_asset_id": best_match["asset"].id,
                "asset_name": best_match["asset"].filename,
                "asset_type": best_match["asset"].category,
                "score": best_match["score"],
                "score_breakdown": best_match["score_breakdown"],
                "signals": signals["signal_snapshot"],
                "need_create_asset": False,
                "suggested_asset_name": suggested_asset_name,
                "suggested_asset_type": suggested_asset_type,
            }
            evidence.asset_match_status = "suggested"
        else:
            evidence.matched_asset_id = None
            evidence.asset_match_score = None
            evidence.asset_match_reasons_json = {
                "summary": ["未找到可确认的测试对象候选"],
                "signals": signals["signal_snapshot"],
                "need_create_asset": True,
                "suggested_asset_name": suggested_asset_name,
                "suggested_asset_type": suggested_asset_type,
            }
            evidence.asset_match_status = "unmatched"
        self.evidence_repository.update(db, evidence)
        return self._get_evidence(db, evidence_id)

    def confirm_asset(self, db, evidence_id: str, asset_id: str | None = None):
        evidence = self._get_evidence(db, evidence_id)
        target_asset_id = asset_id or evidence.matched_asset_id
        if not target_asset_id:
            raise BadRequestException("ASSET_MATCH_NOT_FOUND", "当前证据没有可确认的测试对象")

        asset = self.asset_repository.get(db, target_asset_id)
        if not asset or asset.project_id != evidence.project_id or asset.asset_kind != "test_object":
            raise NotFoundException("MATCHED_ASSET_NOT_FOUND", "测试对象资产不存在")

        evidence.matched_asset_id = asset.id
        evidence.asset_match_status = "confirmed"
        reasons = dict(evidence.asset_match_reasons_json) if isinstance(evidence.asset_match_reasons_json, dict) else {}
        reasons.update(
            {
                "confirmed_asset_id": asset.id,
                "confirmed_asset_name": asset.filename,
                "confirmed_asset_type": asset.category,
            }
        )
        evidence.asset_match_reasons_json = reasons
        self.evidence_repository.update(db, evidence)
        return self._get_evidence(db, evidence_id)

    def _get_evidence(self, db, evidence_id: str):
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")
        return evidence

    def _build_signals(self, evidence, extracted_fields) -> dict[str, Any]:
        full_text = evidence.text_content or ""
        ocr_result = evidence.ocr_result_json if isinstance(evidence.ocr_result_json, dict) else {}
        line_texts = [item.get("text", "") for item in (ocr_result.get("lines") or []) if isinstance(item, dict)]
        signal_text = "\n".join(part for part in [full_text, *line_texts] if part).lower()

        field_values: dict[str, str] = {}
        for field in extracted_fields:
            key = (field.rule_id or field.field_name or "").strip()
            value = (field.corrected_value or field.raw_value or "").strip()
            if key and value:
                field_values[key] = value

        best_name = self._pick_first(field_values, self.NAME_FIELD_CODES) or evidence.device or self._extract_name_from_text(line_texts)
        best_ip = self._pick_first(field_values, self.IP_FIELD_CODES) or self._extract_ip(signal_text)
        suggested_asset_type = self._infer_asset_type(signal_text, best_name)

        return {
            "full_text": signal_text,
            "line_texts": line_texts,
            "field_values": field_values,
            "best_name": best_name,
            "best_ip": best_ip,
            "suggested_asset_type": suggested_asset_type,
            "signal_snapshot": {
                "device_name": best_name,
                "device_ip": best_ip,
                "suggested_asset_type": suggested_asset_type,
                "field_values": field_values,
            },
        }

    def _score_asset(self, asset, signals: dict[str, Any]) -> dict[str, Any]:
        score = 0.0
        summary: list[str] = []
        score_breakdown: dict[str, float] = {}
        normalized_text = self._normalize(signals["full_text"])
        best_name = signals["best_name"]
        best_ip = signals["best_ip"]
        suggested_asset_type = signals["suggested_asset_type"]

        normalized_asset_name = self._normalize(asset.filename)
        if normalized_asset_name and normalized_asset_name in normalized_text:
            score += 5
            score_breakdown["ocr_name_hit"] = 5.0
            summary.append("OCR 文本命中资产名称")
        elif best_name and self._normalize(best_name) == normalized_asset_name:
            score += 6
            score_breakdown["field_name_hit"] = 6.0
            summary.append("抽取字段命中资产名称")
        elif best_name and self._normalize(best_name) in normalized_asset_name:
            score += 3
            score_breakdown["field_name_partial_hit"] = 3.0
            summary.append("抽取字段部分命中资产名称")

        if asset.primary_ip and best_ip and asset.primary_ip == best_ip:
            score += 6
            score_breakdown["ip_hit"] = 6.0
            summary.append("IP 精确命中")
        elif asset.primary_ip and asset.primary_ip in normalized_text:
            score += 5
            score_breakdown["ocr_ip_hit"] = 5.0
            summary.append("OCR 文本命中资产 IP")

        if suggested_asset_type and suggested_asset_type == asset.category:
            score += 2
            score_breakdown["asset_type_hit"] = 2.0
            summary.append("设备类型关键词命中")
        elif suggested_asset_type and suggested_asset_type == self._normalize(asset.category_label):
            score += 2
            score_breakdown["asset_type_label_hit"] = 2.0
            summary.append("设备类型标签命中")

        if not summary:
            tokens = self._extract_tokens(signals["full_text"])
            overlapping = [token for token in tokens if token in normalized_asset_name]
            if overlapping:
                overlap_score = min(2.0, float(len(overlapping)) * 0.5)
                score += overlap_score
                score_breakdown["token_overlap"] = overlap_score
                summary.append("OCR 关键词与资产名称存在重合")

        return {
            "asset": asset,
            "score": round(score, 2),
            "summary": summary,
            "score_breakdown": score_breakdown,
        }

    def _extract_name_from_text(self, line_texts: list[str]) -> str | None:
        for line in line_texts:
            if any(marker in line for marker in ["设备名称", "主机名", "hostname", "HOSTNAME"]):
                parts = re.split(r"[:：]", line, maxsplit=1)
                if len(parts) == 2 and parts[1].strip():
                    return parts[1].strip()
        return None

    def _extract_ip(self, text: str) -> str | None:
        match = self.IP_PATTERN.search(text)
        return match.group(0) if match else None

    def _infer_asset_type(self, text: str, best_name: str | None) -> str | None:
        normalized = f"{text} {(best_name or '').lower()}"
        for keyword, asset_type in self.TYPE_KEYWORDS:
            if keyword.lower() in normalized:
                return asset_type
        if best_name:
            lowered = best_name.lower()
            if lowered.startswith("fw"):
                return "firewall"
            if lowered.startswith("sw") or lowered.startswith("h3c"):
                return "switch"
        return None

    def _pick_first(self, field_values: dict[str, str], keys: set[str]) -> str | None:
        for key in keys:
            value = field_values.get(key)
            if value:
                return value
        return None

    def _extract_tokens(self, text: str) -> list[str]:
        counter: Counter[str] = Counter()
        for token in self.TOKEN_PATTERN.findall(text):
            normalized = self._normalize(token)
            if len(normalized) < 2:
                continue
            counter[normalized] += 1
        return [token for token, _ in counter.most_common(8)]

    def _normalize(self, value: str | None) -> str:
        return re.sub(r"\s+", "", (value or "").strip().lower())
