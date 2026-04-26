from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.evidence_fact import EvidenceFact
from app.repositories.evidence_fact_repository import EvidenceFactRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.extracted_field_repository import ExtractedFieldRepository
from app.services.evidence_page_classifier import EvidencePageClassifier


class EvidenceFactService:
    def __init__(self) -> None:
        self.evidence_repository = EvidenceRepository()
        self.field_repository = ExtractedFieldRepository()
        self.repository = EvidenceFactRepository()
        self.classifier = EvidencePageClassifier()

    def classify_and_extract(
        self,
        db: Session,
        evidence_id: str,
        *,
        ocr_text: str | None = None,
        extracted_fields: Any = None,
    ) -> dict:
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")

        fields = extracted_fields if extracted_fields is not None else self.field_repository.list_by_evidence(db, evidence_id)
        resolved_text = ocr_text or evidence.text_content or self._extract_ocr_text(evidence.ocr_result_json)
        if not resolved_text and not fields:
            raise BadRequestException("EVIDENCE_FACT_INPUT_NOT_FOUND", "证据缺少 OCR 文本和抽取字段，无法识别事实")

        classification = self.classifier.classify(resolved_text, fields)
        page_type = self._normalize_page_type(classification.page_type)
        facts = self._build_facts(evidence, page_type, resolved_text, fields, classification.confidence)
        persisted = self.repository.replace_for_evidence(db, evidence_id, facts)
        return {
            "page_type": page_type,
            "confidence": classification.confidence,
            "reason": classification.reason,
            "matched_keywords": classification.matched_keywords,
            "facts": persisted,
        }

    def list_by_evidence(self, db: Session, evidence_id: str) -> list[EvidenceFact]:
        return self.repository.list_by_evidence(db, evidence_id)

    def _build_facts(self, evidence, page_type: str | None, resolved_text: str, fields: Any, confidence: float) -> list[EvidenceFact]:
        facts: list[EvidenceFact] = []
        field_map = self._field_map(fields)
        facts.append(
            EvidenceFact(
                project_id=evidence.project_id,
                asset_id=evidence.asset_id,
                evidence_id=evidence.id,
                page_type=page_type,
                fact_group="page",
                fact_key="page_type",
                fact_name="页面类型",
                raw_value=page_type,
                normalized_value=page_type,
                source_text=resolved_text[:500] if resolved_text else None,
                confidence=confidence,
                status="identified",
            )
        )

        for key, value in self._extract_rule_facts(page_type, field_map, resolved_text).items():
            facts.append(
                EvidenceFact(
                    project_id=evidence.project_id,
                    asset_id=evidence.asset_id,
                    evidence_id=evidence.id,
                    page_type=page_type,
                    fact_group="extracted",
                    fact_key=key,
                    fact_name=self._fact_name(key),
                    raw_value=str(value) if value is not None else None,
                    normalized_value=str(value) if value is not None else None,
                    value_number=self._to_number(value),
                    value_bool=self._to_bool(value),
                    source_text=field_map.get(f"{key}__source_text") or resolved_text[:500] if resolved_text else None,
                    confidence=confidence,
                    status="identified",
                )
            )
        return facts

    def _extract_rule_facts(self, page_type: str | None, field_map: dict[str, Any], text: str) -> dict[str, Any]:
        facts: dict[str, Any] = {}
        for key in (
            "password_min_length",
            "complexity",
            "password_complexity",
            "password_expire_days",
            "remote_login_status",
            "remote_login_allowed",
            "admin_account_count",
            "log_retention_days",
            "signature_version",
            "virus_database_version",
            "asset_ip",
            "device_ip",
            "ip",
            "asset_version",
            "version",
            "command",
            "page_name",
            "compliance_result",
            "compliance_status",
        ):
            value = field_map.get(key)
            if value not in (None, ""):
                facts[key] = value

        lowered = (text or "").lower()
        if page_type == "password_policy" and "password_min_length" not in facts:
            for token in ("最小密码长度", "密码长度", "最短长度"):
                if token in text:
                    facts["page_name"] = facts.get("page_name") or "管理员账号-密码安全策略"
                    break
        if page_type in {"login_policy", "login_failure_lock"}:
            facts["page_name"] = facts.get("page_name") or "管理员账号-登录策略"
        if any(token in lowered for token in ("show ", "display ", "system-view", "cat /etc/", "grep ")):
            facts["command"] = facts.get("command") or self._extract_command_line(text)
        return facts

    def _field_map(self, fields: Any) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for field in fields or []:
            key = getattr(field, "rule_id", None) or getattr(field, "field_name", None)
            if not key:
                continue
            result[key] = getattr(field, "corrected_value", None) or getattr(field, "raw_value", None)
            source_text = getattr(field, "source_text", None)
            if source_text:
                result[f"{key}__source_text"] = source_text
        return result

    def _normalize_page_type(self, page_type: str | None) -> str:
        mapping = {
            "login_failure_lock": "login_policy",
            "admin_account": "account_list",
            "user_role_permission": "access_control",
            "audit_log": "security_audit",
            "system_log": "security_audit",
            "remote_management_protocol": "network_config",
            "security_policy": "firewall_policy",
            "access_control_policy": "firewall_policy",
            "system_version": "system_config",
        }
        if not page_type:
            return "unknown"
        return mapping.get(page_type, page_type)

    def _extract_ocr_text(self, payload: Any) -> str:
        if isinstance(payload, dict):
            return str(payload.get("full_text") or "")
        return ""

    def _extract_command_line(self, text: str) -> str | None:
        for line in (text or "").splitlines():
            lowered = line.lower()
            if any(token in lowered for token in ("show ", "display ", "system-view", "cat /etc/", "grep ")):
                return line.strip()
        return None

    def _fact_name(self, key: str) -> str:
        return {
            "password_min_length": "密码最小长度",
            "complexity": "密码复杂度",
            "password_complexity": "密码复杂度",
            "password_expire_days": "口令有效期",
            "remote_login_status": "远程登录状态",
            "remote_login_allowed": "远程登录状态",
            "admin_account_count": "管理员账户数量",
            "log_retention_days": "日志保留时间",
            "signature_version": "病毒库版本",
            "virus_database_version": "病毒库版本",
            "asset_ip": "资产IP",
            "device_ip": "设备IP",
            "ip": "设备IP",
            "asset_version": "资产版本",
            "version": "资产版本",
            "command": "执行命令",
            "page_name": "页面名称",
            "compliance_result": "符合情况",
            "compliance_status": "符合情况",
        }.get(key, key)

    def _to_number(self, value: Any) -> float | None:
        try:
            if value in (None, ""):
                return None
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
