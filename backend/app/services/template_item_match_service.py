from __future__ import annotations

import re
from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.assessment_template import AssessmentTemplateItem
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.extracted_field_repository import ExtractedFieldRepository
from app.repositories.history_record_repository import HistoryRecordRepository
from app.services.assessment_template_service import AssessmentTemplateService
from app.services.evidence_page_classifier import EvidencePageClassifier


class TemplateItemMatchService:
    TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_./:-]{2,}|[一-鿿]{2,}")
    COMMAND_PATTERNS = (
        re.compile(r"\b(?:display|show|cat|grep|net\s+user|secpol\.msc|gpedit\.msc|system-view|syslog)\b[^\n，。；]{0,80}", re.IGNORECASE),
        re.compile(r"/etc/[A-Za-z0-9_./-]+", re.IGNORECASE),
    )
    RELATED_PAGE_TYPES = {
        "password_policy": {"login_failure_lock"},
        "login_failure_lock": {"password_policy"},
        "audit_log": {"system_log", "log_server_config"},
        "system_log": {"audit_log"},
        "log_server_config": {"audit_log", "system_log"},
        "access_control_policy": {"security_policy"},
        "security_policy": {"access_control_policy"},
    }
    OBJECT_TYPE_TO_ASSET_TYPE = {
        "安全设备": "firewall",
        "网络设备": "switch",
        "服务器": "server",
        "数据库": "database",
        "中间件": "middleware",
        "应用系统": "application",
        "数据对象": "data",
        "管理制度": "management",
        "管理对象": "management",
        "通信网络": "network",
        "物理环境": "physical",
        "区域边界": "boundary",
    }
    OBJECT_CATEGORY_TO_ASSET_TYPE = {
        "防火墙": "firewall",
        "交换机": "switch",
        "windows": "server",
        "linux": "server",
        "数据库": "database",
        "中间件": "middleware",
        "应用系统": "application",
    }
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
    }

    def __init__(self) -> None:
        self.evidence_repository = EvidenceRepository()
        self.field_repository = ExtractedFieldRepository()
        self.history_repository = HistoryRecordRepository()
        self.template_service = AssessmentTemplateService()
        self.classifier = EvidencePageClassifier()

    def match(
        self,
        db: Session,
        evidence_id: str,
        *,
        ocr_text: str | None = None,
        page_type: str | None = None,
        asset_type: str | None = None,
        extracted_fields: Any = None,
        evidence_facts: Any = None,
    ) -> dict:
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")

        workbooks = self.template_service.list_workbooks(db)
        if not workbooks:
            raise BadRequestException("ASSESSMENT_TEMPLATE_LIBRARY_EMPTY", "测评记录模板库为空，请先导入模板")

        active_workbook = workbooks[0]
        items = self.template_service.list_items(db, workbook_id=active_workbook.id)
        if not items:
            raise BadRequestException("ASSESSMENT_TEMPLATE_LIBRARY_EMPTY", "当前模板工作簿没有可匹配的模板项")

        fields = self.field_repository.list_by_evidence(db, evidence_id)
        resolved_text = self._resolve_ocr_text(evidence, ocr_text)
        resolved_fields = extracted_fields if extracted_fields is not None else fields
        resolved_facts = self._resolve_evidence_facts(evidence_facts, resolved_fields)
        if not resolved_text and not resolved_fields and not resolved_facts:
            raise BadRequestException("EVIDENCE_TEMPLATE_MATCH_INPUT_NOT_FOUND", "证据缺少 OCR 文本、抽取字段或事实线索，无法匹配模板项")

        classification = self.classifier.classify(resolved_text, resolved_fields)
        resolved_page_type = page_type or classification.page_type
        if resolved_page_type and resolved_page_type not in self.classifier.PAGE_TYPE_KEYWORDS:
            raise BadRequestException("EVIDENCE_PAGE_TYPE_INVALID", "页面类型不支持")
        resolved_asset_type = asset_type or self._resolve_asset_type(evidence)
        control_point_counts = self._build_control_point_counts(db, resolved_asset_type)

        candidates = [
            self._score_item(
                item,
                ocr_text=resolved_text,
                page_type=resolved_page_type,
                asset_type=resolved_asset_type,
                evidence_facts=resolved_facts,
                control_point_counts=control_point_counts,
            )
            for item in items
        ]
        candidates = [item for item in candidates if item["score"] > 0]
        candidates = sorted(candidates, key=lambda item: (-item["score"], item["sheet_name"], item["row_index"]))[:5]
        best = candidates[0] if candidates else None
        score = best["score"] if best else 0.0
        confidence = self._build_confidence(score, candidates)
        return {
            "matched_template_item": best,
            "candidates": candidates,
            "score": score,
            "confidence": confidence,
            "reason": self._build_reason(best, classification, resolved_page_type, active_workbook.name),
        }

    def _score_item(
        self,
        item: AssessmentTemplateItem,
        *,
        ocr_text: str,
        page_type: str | None,
        asset_type: str | None,
        evidence_facts: list[str],
        control_point_counts: dict[str, int],
    ) -> dict:
        score = 0.0
        reasons: list[str] = []
        matched_keywords: list[str] = []
        metadata = self._build_template_metadata(item)

        template_asset_type = self._infer_template_asset_type(item)
        if asset_type and template_asset_type and asset_type == template_asset_type:
            score += 0.25
            reasons.append("资产类型命中模板对象类型")

        template_page_types = [str(value).lower() for value in self._as_string_list(item.page_types_json)]
        if page_type and page_type in template_page_types:
            score += 0.25
            reasons.append("页面类型命中模板页面类型")
        elif page_type and any(related in template_page_types for related in self.RELATED_PAGE_TYPES.get(page_type, set())):
            score += 0.18
            reasons.append("页面类型命中相邻模板页面类型")

        record_hits = self._collect_hits(
            ocr_text,
            metadata["page_keywords"] + metadata["command_keywords"] + metadata["fact_keywords"] + metadata["record_tokens"],
        )
        if record_hits:
            hit_score = 0.2 * min(1.0, len(record_hits) / 4)
            score += hit_score
            reasons.append(f"OCR 命中结果记录模板关键词 {len(record_hits)} 个")
            matched_keywords.extend(record_hits[:8])

        item_hits = self._collect_hits(ocr_text, self._item_keywords(item))
        if item_hits:
            hit_score = 0.15 * min(1.0, len(item_hits) / 3)
            score += hit_score
            reasons.append(f"OCR 命中测评项/控制点关键词 {len(item_hits)} 个")
            matched_keywords.extend(item_hits[:8])

        fact_hits = self._collect_hits(" ".join(evidence_facts), metadata["fact_keywords"] + self._as_string_list(item.required_facts_json))
        if fact_hits:
            hit_score = 0.1 * min(1.0, len(fact_hits) / 2)
            score += hit_score
            reasons.append(f"事实线索命中必备事实 {len(fact_hits)} 个")
            matched_keywords.extend(fact_hits[:8])

        bonus = self._build_bonus(item, ocr_text, evidence_facts, control_point_counts, bool(record_hits or item_hits or fact_hits))
        if bonus > 0:
            score += bonus
            reasons.append("编号/历史控制点频次加分")

        unique_keywords = list(dict.fromkeys(keyword for keyword in matched_keywords if keyword))[:8]
        normalized_score = round(min(score, 0.99), 2)
        return {
            "id": item.id,
            "sheet_name": item.sheet_name,
            "row_index": item.row_index,
            "item_code": item.item_code,
            "object_type": item.object_type,
            "object_category": item.object_category,
            "control_point": item.control_point,
            "item_text": item.item_text,
            "record_template": item.record_template,
            "default_compliance_result": item.default_compliance_result,
            "page_types_json": self._as_string_list(item.page_types_json),
            "score": normalized_score,
            "reasons": reasons,
            "matched_keywords": unique_keywords,
        }

    def _resolve_ocr_text(self, evidence, override: str | None) -> str:
        if override:
            return override
        if evidence.text_content:
            return evidence.text_content
        if isinstance(evidence.ocr_result_json, dict):
            return str(evidence.ocr_result_json.get("full_text") or "")
        return ""

    def _resolve_evidence_facts(self, evidence_facts: Any, extracted_fields: Any) -> list[str]:
        flattened = self._flatten(evidence_facts)
        if flattened:
            return flattened
        return [value for value in self._flatten(extracted_fields) if value]

    def _resolve_asset_type(self, evidence) -> str | None:
        if evidence.matched_asset:
            return evidence.matched_asset.category
        reasons = evidence.asset_match_reasons_json if isinstance(evidence.asset_match_reasons_json, dict) else {}
        value = reasons.get("suggested_asset_type") or reasons.get("asset_type")
        return str(value) if value else None

    def _build_control_point_counts(self, db: Session, asset_type: str | None) -> dict[str, int]:
        rows = self.history_repository.list_all(db)
        counter: Counter[str] = Counter()
        for row in rows:
            if asset_type and row.asset_type and row.asset_type != asset_type:
                continue
            if row.control_point:
                counter[row.control_point] += 1
        return dict(counter)

    def _build_bonus(
        self,
        item: AssessmentTemplateItem,
        ocr_text: str,
        evidence_facts: list[str],
        control_point_counts: dict[str, int],
        has_primary_match: bool,
    ) -> float:
        normalized_text = self._normalize(ocr_text)
        normalized_facts = self._normalize(" ".join(evidence_facts))
        if item.item_code and self._normalize(item.item_code) in {normalized_text, normalized_facts}:
            return 0.05
        if item.item_code and self._normalize(item.item_code) and self._normalize(item.item_code) in normalized_text:
            return 0.05
        if not has_primary_match or not item.control_point or not control_point_counts:
            return 0.0
        max_count = max(control_point_counts.values(), default=0)
        current = control_point_counts.get(item.control_point, 0)
        if max_count <= 0 or current <= 0:
            return 0.0
        return round(0.05 * (current / max_count), 2)

    def _build_confidence(self, score: float, candidates: list[dict]) -> float:
        if not score:
            return 0.0
        second = candidates[1]["score"] if len(candidates) > 1 else 0.0
        margin = max(score - second, 0.0)
        return round(min(0.99, score + margin * 0.2), 2)

    def _build_reason(
        self,
        best: dict | None,
        classification,
        page_type: str | None,
        workbook_name: str,
    ) -> list[str]:
        if not best:
            return [
                f"当前模板工作簿：{workbook_name}",
                f"页面类型：{page_type or classification.page_type or '未识别'}",
                "未命中可确认的结果记录模板项",
            ]
        reasons = [f"当前模板工作簿：{workbook_name}"]
        if page_type or classification.page_type:
            reasons.append(f"页面类型：{page_type or classification.page_type}")
        reasons.append(f"最佳候选分数 {best['score']}")
        reasons.extend(best["reasons"][:4])
        return reasons

    def _build_template_metadata(self, item: AssessmentTemplateItem) -> dict[str, list[str]]:
        record_template = item.record_template or ""
        page_keywords = self._extract_page_keywords(record_template, self._as_string_list(item.page_types_json))
        command_keywords = self._extract_command_keywords(record_template)
        fact_keywords = list(
            dict.fromkeys(
                self._extract_fact_keywords(record_template)
                + self._as_string_list(item.required_facts_json)
                + self._as_string_list(item.evidence_keywords_json)
            )
        )
        record_tokens = self._extract_tokens(record_template)
        return {
            "page_keywords": page_keywords,
            "command_keywords": command_keywords,
            "fact_keywords": fact_keywords,
            "record_tokens": record_tokens,
        }

    def _extract_page_keywords(self, record_template: str, page_types: list[str]) -> list[str]:
        hits: list[str] = []
        lowered = record_template.lower()
        for page_type in page_types:
            for keyword in self.classifier.PAGE_TYPE_KEYWORDS.get(page_type, ()):
                if keyword.lower() in lowered and keyword not in hits:
                    hits.append(keyword)
        return hits[:12]

    def _extract_command_keywords(self, record_template: str) -> list[str]:
        commands: list[str] = []
        for pattern in self.COMMAND_PATTERNS:
            for match in pattern.findall(record_template or ""):
                value = str(match).strip()
                if value and value not in commands:
                    commands.append(value)
        return commands[:8]

    def _extract_fact_keywords(self, record_template: str) -> list[str]:
        hits: list[str] = []
        lowered = (record_template or "").lower()
        for keywords in self.classifier.PAGE_TYPE_KEYWORDS.values():
            for keyword in keywords:
                if keyword.lower() in lowered and keyword not in hits:
                    hits.append(keyword)
        return hits[:12]

    def _item_keywords(self, item: AssessmentTemplateItem) -> list[str]:
        return list(
            dict.fromkeys(
                self._extract_tokens(item.control_point or "")
                + self._extract_tokens(item.item_text or "")
                + self._as_string_list(item.command_keywords_json)
            )
        )[:12]

    def _infer_template_asset_type(self, item: AssessmentTemplateItem) -> str | None:
        if item.object_category:
            lowered_category = item.object_category.lower()
            value = self.OBJECT_CATEGORY_TO_ASSET_TYPE.get(lowered_category)
            if value:
                return value
        if item.object_type:
            value = self.OBJECT_TYPE_TO_ASSET_TYPE.get(item.object_type)
            if value:
                return value
        lowered_sheet = (item.sheet_name or "").lower()
        if "防火墙" in lowered_sheet:
            return "firewall"
        if "交换机" in lowered_sheet:
            return "switch"
        if "windows" in lowered_sheet or "linux" in lowered_sheet or "服务器" in lowered_sheet:
            return "server"
        return None

    def _collect_hits(self, source_text: str, candidates: list[str | None]) -> list[str]:
        normalized_source = self._normalize(source_text)
        hits: list[str] = []
        for candidate in candidates:
            normalized_candidate = self._normalize(candidate)
            if len(normalized_candidate) < 2:
                continue
            if normalized_candidate in normalized_source:
                if candidate not in hits:
                    hits.append(str(candidate))
        return hits

    def _extract_tokens(self, text: str) -> list[str]:
        counter: Counter[str] = Counter()
        for token in self.TOKEN_PATTERN.findall(text or ""):
            normalized = self._normalize(token)
            if len(normalized) < 2 or normalized in self.STOPWORDS:
                continue
            counter[str(token).strip()] += 1
        return [token for token, _ in counter.most_common(12)]

    def _as_string_list(self, value: Any) -> list[str]:
        return [str(item) for item in value] if isinstance(value, list) else []

    def _flatten(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            result: list[str] = []
            for item in value.values():
                result.extend(self._flatten(item))
            return result
        if isinstance(value, list | tuple | set):
            result: list[str] = []
            for item in value:
                result.extend(self._flatten(item))
            return result
        for attr in ("corrected_value", "raw_value", "field_name"):
            if hasattr(value, attr):
                current = getattr(value, attr)
                if current:
                    return [str(current)]
        return [str(value)]

    def _normalize(self, value: str | None) -> str:
        return re.sub(r"\s+", "", (value or "").strip().lower())
