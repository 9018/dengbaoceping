from __future__ import annotations

import re
from typing import Any

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.extracted_field import ExtractedField
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.extracted_field_repository import ExtractedFieldRepository
from app.services.rule_loader import RuleLoader


class FieldExtractionService:
    def __init__(self) -> None:
        self.evidence_repository = EvidenceRepository()
        self.field_repository = ExtractedFieldRepository()
        self.rule_loader = RuleLoader()

    def extract_fields(self, db, evidence_id: str, template_code: str | None = None):
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")
        if not evidence.text_content:
            raise BadRequestException("OCR_TEXT_NOT_FOUND", "请先执行OCR再进行字段抽取")

        rules = self.rule_loader.get_rules_by_template(template_code) if template_code else self.rule_loader.load_field_rules()
        extracted_fields: list[ExtractedField] = []
        for rule in rules:
            result = self._apply_rule(evidence.text_content, rule)
            extracted_fields.append(
                ExtractedField(
                    project_id=evidence.project_id,
                    asset_id=evidence.asset_id,
                    evidence_id=evidence.id,
                    field_group=rule.get("field_group", "basic"),
                    field_name=rule.get("field_name", rule["field_code"]),
                    raw_value=result["raw_value"],
                    corrected_value=result["corrected_value"],
                    source_text=result["source_text"],
                    status=result["status"],
                    rule_id=rule["field_code"],
                    field_value_text=result["corrected_value"] if rule.get("value_type") == "text" else None,
                    field_value_number=self._to_number(result["corrected_value"]) if rule.get("value_type") == "number" else None,
                    field_value_bool=self._to_bool(result["corrected_value"]) if rule.get("value_type") == "bool" else None,
                    field_value_json=result["corrected_value"] if rule.get("value_type") == "json" else None,
                    source_page=1,
                    confidence=result["confidence"],
                )
            )

        self.field_repository.delete_by_evidence(db, evidence.id)
        return self.field_repository.bulk_create(db, extracted_fields)

    def list_fields(self, db, evidence_id: str):
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")
        return self.field_repository.list_by_evidence(db, evidence_id)

    def _apply_rule(self, text: str, rule: dict[str, Any]) -> dict[str, Any]:
        normalized_text = self._normalize_document(text, rule)
        for pattern in rule.get("regex", []):
            match = re.search(pattern, normalized_text, flags=re.MULTILINE)
            if match:
                raw_value = match.group("value").strip()
                corrected_value = self._normalize_value(raw_value, rule)
                status = "corrected" if corrected_value != raw_value else "extracted"
                return {
                    "raw_value": raw_value,
                    "corrected_value": corrected_value,
                    "source_text": match.group(0),
                    "status": status,
                    "confidence": 0.95 if status == "corrected" else 0.98,
                }
        return {
            "raw_value": None,
            "corrected_value": None,
            "source_text": None,
            "status": rule.get("status_when_missing", "missing"),
            "confidence": 0.0,
        }

    def _normalize_document(self, text: str, rule: dict[str, Any]) -> str:
        result = text
        replace_map = rule.get("normalize", {}).get("replace", {})
        for src, dst in replace_map.items():
            result = result.replace(src, dst)
        return result

    def _normalize_value(self, value: str, rule: dict[str, Any]) -> Any:
        result = value.strip()
        if rule.get("normalize", {}).get("collapse_spaces"):
            result = re.sub(r"\s+", " ", result)
        tolerance = rule.get("ocr_tolerance", {})
        if tolerance.get("enabled"):
            char_map = tolerance.get("char_map", {})
            for src, dst in char_map.items():
                result = result.replace(src, dst)
        replace_map = rule.get("normalize", {}).get("replace", {})
        for src, dst in replace_map.items():
            result = result.replace(src, dst)
        return result.strip()

    def _to_number(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_bool(self, value: Any) -> bool | None:
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"true", "yes", "enabled", "是", "已启用", "开启"}:
            return True
        if normalized in {"false", "no", "disabled", "否", "未启用", "关闭"}:
            return False
        return None
