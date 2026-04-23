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
        return {
            "device_type": device_type,
            "field_map": field_map,
            "candidates": ranked,
            "best_match": best_match,
        }

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
        matched_required = [field for field in required_fields if field_map.get(field)]
        missing_fields = [field for field in required_fields if not field_map.get(field)]
        required_score = len(matched_required) / len(required_fields) if required_fields else 1.0

        allowed_types = [entry.lower() for entry in item.get("device_types", [])]
        if not allowed_types:
            device_type_score = 1.0
            device_reason = "未配置设备类型限制"
        elif not device_type:
            device_type_score = 0.3
            device_reason = "未识别设备类型，按弱匹配计分"
        elif device_type in allowed_types:
            device_type_score = 1.0
            device_reason = f"设备类型匹配：{device_type}"
        else:
            device_type_score = 0.0
            device_reason = f"设备类型冲突：{device_type}，期望 {', '.join(allowed_types)}"

        weights = item.get("match_weights", {})
        score = round(
            required_score * float(weights.get("required_fields", 0.0))
            + device_type_score * float(weights.get("device_type", 0.0)),
            4,
        )

        matched_field_records = []
        matched_field_ids: list[str] = []
        for field in fields:
            key = field.rule_id or field.field_name
            if key in matched_required and (field.corrected_value or field.raw_value):
                matched_field_records.append(
                    {
                        "field_code": key,
                        "field_name": field.field_name,
                        "value": field.corrected_value or field.raw_value,
                        "status": field.status,
                    }
                )
                matched_field_ids.append(field.id)

        reasons = {
            "matched_required_fields": matched_required,
            "missing_required_fields": missing_fields,
            "device_type": device_type,
            "device_type_reason": device_reason,
            "required_fields_score": round(required_score, 4),
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
            "missing_fields": missing_fields,
        }
