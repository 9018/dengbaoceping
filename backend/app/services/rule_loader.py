from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import BadRequestException


class RuleLoader:
    def __init__(self) -> None:
        self.rules_dir = Path(settings.BASE_DIR / "app" / "rules") if hasattr(settings, "BASE_DIR") else Path(settings.UPLOAD_DIR).parent / "app" / "rules"
        self._cache: dict[str, list[dict]] = {}

    def _load_json(self, filename: str):
        if filename in self._cache:
            return self._cache[filename]
        path = self.rules_dir / filename
        if not path.exists():
            self._cache[filename] = []
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        self._cache[filename] = data
        return data

    def load_field_rules(self):
        rules = self._load_json("field_rules.json")
        for rule in rules:
            missing_keys = {"field_code", "aliases", "regex", "normalize"} - set(rule.keys())
            if missing_keys:
                raise BadRequestException("INVALID_FIELD_RULE", "字段规则定义不完整", sorted(missing_keys))
        return rules

    def load_evaluation_items(self):
        items = self._load_json("evaluation_items.json")
        for item in items:
            missing_keys = {"item_code", "template_code", "required_fields", "device_types", "match_weights", "pass_score"} - set(item.keys())
            if missing_keys:
                raise BadRequestException("INVALID_EVALUATION_ITEM_RULE", "测评条目规则定义不完整", sorted(missing_keys))
        return items

    def load_templates(self):
        templates = self._load_json("templates.json")
        for template in templates:
            missing_keys = {"template_code", "name", "template_type", "field_codes", "generation"} - set(template.keys())
            if missing_keys:
                raise BadRequestException("INVALID_TEMPLATE_RULE", "模板规则定义不完整", sorted(missing_keys))
            generation = template.get("generation") or {}
            generation_missing_keys = {"title_template", "record_template", "fallbacks", "default_review_comment"} - set(generation.keys())
            if generation_missing_keys:
                raise BadRequestException("INVALID_TEMPLATE_GENERATION_RULE", "模板生成规则定义不完整", sorted(generation_missing_keys))
        return templates

    def get_rules_by_template(self, template_code: str | None):
        if not template_code:
            return self.load_field_rules()
        template = self.get_template(template_code)
        field_codes = set(template.get("field_codes", []))
        return [rule for rule in self.load_field_rules() if rule.get("field_code") in field_codes]

    def get_template(self, template_code: str):
        template = next((item for item in self.load_templates() if item.get("template_code") == template_code), None)
        if not template:
            raise BadRequestException("TEMPLATE_NOT_FOUND", "指定模板不存在")
        return template

    def get_evaluation_items(self):
        return self.load_evaluation_items()

    def get_evaluation_item(self, item_code: str):
        item = next((entry for entry in self.load_evaluation_items() if entry.get("item_code") == item_code), None)
        if not item:
            raise BadRequestException("EVALUATION_ITEM_NOT_FOUND", "指定测评条目不存在")
        return item
