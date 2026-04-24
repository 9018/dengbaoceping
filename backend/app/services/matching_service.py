from __future__ import annotations

from app.models.extracted_field import ExtractedField
from app.services.rule_loader import RuleLoader


class MatchingService:
    def __init__(self) -> None:
        self.rule_loader = RuleLoader()

    def match(self, fields: list[ExtractedField], device_type_override: str | None = None) -> dict:
        field_map = self._build_field_map(fields)
        device_type = self._resolve_device_type(field_map, device_type_override)
        items = self.rule_loader.get_evaluation_items()
        ranked = [self._score_item(item, fields, field_map, device_type) for item in items]
        ranked.sort(key=lambda item: item["score"], reverse=True)
        best_match = ranked[0] if ranked else None
        top_candidates = ranked[:3]
        return {
            "device_type": device_type,
            "field_map": field_map,
            "candidates": ranked,
            "top_candidates": top_candidates,
            "best_match": best_match,
        }

    def select_candidate(
        self,
        match_result: dict,
        selected_item_code: str | None = None,
        selected_template_code: str | None = None,
    ) -> dict | None:
        candidates = match_result.get("candidates") or []
        if selected_item_code:
            candidate = next((item for item in candidates if item["item_code"] == selected_item_code), None)
            if candidate:
                return candidate
            return None
        if selected_template_code:
            candidate = next((item for item in candidates if item["template_code"] == selected_template_code), None)
            if candidate:
                return candidate
            return None
        return match_result.get("best_match")

    def _build_field_map(self, fields: list[ExtractedField]) -> dict[str, str | None]:
        field_map: dict[str, str | None] = {}
        for field in fields:
            key = field.rule_id or field.field_name
            field_map[key] = field.corrected_value or field.raw_value
        return field_map

    def _resolve_device_type(self, field_map: dict[str, str | None], device_type_override: str | None) -> str | None:
        if device_type_override:
            return device_type_override.strip().lower()
        name = (field_map.get("device_name") or field_map.get("hostname") or "").lower()
        if name.startswith("fw"):
            return "firewall"
        if name.startswith("win") or name.startswith("srv"):
            return "server"
        return None

    def _score_item(
        self,
        item: dict,
        fields: list[ExtractedField],
        field_map: dict[str, str | None],
        device_type: str | None,
    ) -> dict:
        required_fields = item.get("required_fields", [])
        optional_fields = item.get("optional_fields", [])
        negative_fields = item.get("negative_fields", [])
        template = self.rule_loader.get_template(item["template_code"])
        template_field_codes = template.get("field_codes", [])
        template_field_set = set(template_field_codes)

        matched_required = [field for field in required_fields if field_map.get(field)]
        missing_required = [field for field in required_fields if not field_map.get(field)]
        matched_optional = [field for field in optional_fields if field_map.get(field)]
        missing_optional = [field for field in optional_fields if not field_map.get(field)]
        matched_negative = [field for field in negative_fields if field_map.get(field)]
        clean_negative = [field for field in negative_fields if not field_map.get(field)]
        matched_template_fields = [field for field in template_field_codes if field_map.get(field)]
        missing_template_fields = [field for field in template_field_codes if not field_map.get(field)]

        required_score = len(matched_required) / len(required_fields) if required_fields else 1.0
        optional_score = len(matched_optional) / len(optional_fields) if optional_fields else 1.0
        negative_score = len(clean_negative) / len(negative_fields) if negative_fields else 1.0
        template_coverage = len(matched_template_fields) / len(template_field_codes) if template_field_codes else 1.0

        allowed_types = [entry.lower() for entry in item.get("device_types", [])]
        if not allowed_types:
            device_type_score = 1.0
            device_reason = "未配置设备类型限制"
        elif not device_type:
            device_type_score = 0.3
            device_reason = "未识别设备类型，按弱匹配计分"
        elif device_type in allowed_types:
            device_type_score = 1.0
            device_reason = f"设备类型匹配: {device_type}"
        else:
            device_type_score = 0.0
            device_reason = f"设备类型冲突: {device_type}，期望 {', '.join(allowed_types)}"

        weights = item.get("match_weights", {})
        score = round(
            required_score * float(weights.get("required_fields", 0.0))
            + optional_score * float(weights.get("optional_fields", 0.0))
            + negative_score * float(weights.get("negative_fields", 0.0))
            + template_coverage * float(weights.get("template_coverage", 0.0))
            + device_type_score * float(weights.get("device_type", 0.0)),
            4,
        )
        if template_field_set and not set(field_map.keys()).intersection(template_field_set):
            score = 0.0

        matched_field_records = []
        matched_field_ids: list[str] = []
        relevant_fields = set(matched_required)
        for field in fields:
            key = field.rule_id or field.field_name
            if key in relevant_fields and (field.corrected_value or field.raw_value):
                matched_field_records.append(
                    {
                        "field_code": key,
                        "field_name": field.field_name,
                        "value": field.corrected_value or field.raw_value,
                        "status": field.status,
                    }
                )
                matched_field_ids.append(field.id)

        reasons_text = [f"命中 required field: {field}" for field in matched_required]
        reasons_text.extend(f"缺失字段: {field}" for field in missing_required)
        reasons_text.extend(f"命中 optional field: {field}" for field in matched_optional)
        reasons_text.extend(f"未命中 optional field: {field}" for field in missing_optional)
        reasons_text.extend(f"命中 negative field: {field}" for field in matched_negative)
        reasons_text.extend(f"模板字段覆盖: {field}" for field in matched_template_fields)
        reasons_text.append(device_reason)

        reasons = {
            "summary": reasons_text,
            "matched_required_fields": matched_required,
            "missing_required_fields": missing_required,
            "matched_optional_fields": matched_optional,
            "missing_optional_fields": missing_optional,
            "matched_negative_fields": matched_negative,
            "clean_negative_fields": clean_negative,
            "matched_template_fields": matched_template_fields,
            "missing_template_fields": missing_template_fields,
            "device_type": device_type,
            "device_type_reason": device_reason,
            "required_fields_score": round(required_score, 4),
            "optional_fields_score": round(optional_score, 4),
            "negative_fields_score": round(negative_score, 4),
            "template_coverage": round(template_coverage, 4),
            "device_type_score": round(device_type_score, 4),
            "pass_score": float(item.get("pass_score", 0.0)),
            "domain": item.get("domain"),
            "level2": item.get("level2"),
            "level3": item.get("level3"),
        }
        return {
            "item_code": item["item_code"],
            "template_code": item["template_code"],
            "domain": item.get("domain"),
            "level2": item.get("level2"),
            "level3": item.get("level3"),
            "score": score,
            "pass_score": float(item.get("pass_score", 0.0)),
            "reasons": reasons,
            "matched_fields": matched_field_records,
            "matched_field_ids": matched_field_ids,
            "missing_fields": missing_required,
        }
