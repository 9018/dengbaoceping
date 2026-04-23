from __future__ import annotations

from app.core.exceptions import BadRequestException
from app.services.rule_loader import RuleLoader


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


class TemplateService:
    def __init__(self) -> None:
        self.rule_loader = RuleLoader()

    def render(self, template_code: str, field_map: dict[str, str | None], missing_fields: list[str]) -> dict:
        template = self.rule_loader.get_template(template_code)
        generation = template.get("generation") or {}
        values = self._build_render_values(field_map, generation.get("fallbacks") or {})
        title = self._render_template(generation.get("title_template", ""), values)
        record_content = self._render_template(generation.get("record_template", ""), values)
        review_comment = generation.get("default_review_comment") or ""
        if missing_fields:
            review_comment = f"{review_comment} 缺失字段: {', '.join(missing_fields)}。".strip()
        return {
            "title": title,
            "record_content": record_content,
            "review_comment": review_comment,
        }

    def _build_render_values(self, field_map: dict[str, str | None], fallbacks: dict[str, str]) -> dict[str, str]:
        values: dict[str, str] = {}
        keys = set(field_map.keys()) | set(fallbacks.keys())
        for key in keys:
            values[key] = field_map.get(key) or fallbacks.get(key) or f"[待补充: {key}]"
        return values

    def _render_template(self, template: str, values: dict[str, str]) -> str:
        try:
            return template.format_map(_SafeDict(values))
        except ValueError as exc:
            raise BadRequestException("INVALID_TEMPLATE_FORMAT", "模板格式不合法", str(exc)) from exc
