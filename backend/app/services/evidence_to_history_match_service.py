from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.history_record import HistoryRecord
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.extracted_field_repository import ExtractedFieldRepository
from app.repositories.history_record_repository import HistoryRecordRepository
from app.services.evidence_page_classifier import EvidencePageClassifier


class EvidenceToHistoryMatchService:
    PAGE_TYPE_HISTORY_KEYWORDS: dict[str, tuple[str, ...]] = {
        "password_policy": ("身份鉴别", "复杂度", "定期更换", "口令", "密码"),
        "login_failure_lock": ("身份鉴别", "登录失败", "非法登录", "锁定"),
        "session_timeout": ("身份鉴别", "超时", "会话", "自动退出"),
        "remote_management_protocol": ("身份鉴别", "远程管理", "https", "ssh", "telnet"),
        "admin_account": ("身份鉴别", "管理员", "管理账户", "唯一性"),
        "user_role_permission": ("访问控制", "权限", "角色", "授权"),
        "access_control_policy": ("访问控制", "系统边界", "安全策略", "源地址", "目的地址", "默认拒绝"),
        "security_policy": ("访问控制", "安全策略", "规则"),
        "intrusion_prevention": ("入侵防范", "入侵防御", "威胁防护"),
        "antivirus": ("恶意代码", "防病毒", "病毒库"),
        "audit_log": ("安全审计", "审计日志", "操作日志"),
        "system_log": ("安全审计", "系统日志", "日志"),
        "log_server_config": ("安全审计", "日志服务器", "日志转发"),
        "signature_update": ("恶意代码", "特征库", "签名库", "更新"),
        "system_version": ("系统版本", "版本", "升级"),
        "ha_status": ("高可用", "双机", "主备", "冗余"),
    }
    TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{3,}|[一-鿿]{2,}")

    def __init__(self) -> None:
        self.evidence_repository = EvidenceRepository()
        self.field_repository = ExtractedFieldRepository()
        self.history_repository = HistoryRecordRepository()
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
    ) -> dict:
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")
        fields = self.field_repository.list_by_evidence(db, evidence_id)
        resolved_text = self._resolve_ocr_text(evidence, ocr_text)
        resolved_fields = extracted_fields if extracted_fields is not None else fields
        if not resolved_text and not resolved_fields:
            raise BadRequestException("EVIDENCE_HISTORY_MATCH_INPUT_NOT_FOUND", "证据缺少 OCR 文本或抽取字段，无法匹配历史记录")
        classification = self.classifier.classify(resolved_text, resolved_fields)
        resolved_page_type = page_type or classification.page_type
        if resolved_page_type and resolved_page_type not in self.classifier.PAGE_TYPE_KEYWORDS:
            raise BadRequestException("EVIDENCE_PAGE_TYPE_INVALID", "页面类型不支持")
        resolved_asset_type = asset_type or self._resolve_asset_type(evidence)
        history_records = self.history_repository.list_all(db)
        results = [self._score_record(record, resolved_text, resolved_page_type, resolved_asset_type, resolved_fields) for record in history_records]
        matched = [item for item in results if item["score"] > 0]
        matched = sorted(matched, key=lambda item: (-item["score"], item["sheet_name"], item["asset_name"]))[:5]
        best = matched[0] if matched else None
        confidence = best["score"] if best else 0.0
        return {
            "matched_history_records": matched,
            "suggested_control_point": best["control_point"] if best else None,
            "suggested_item_text": best["item_text"] if best else None,
            "suggested_record_text": best["record_text"] if best else None,
            "suggested_compliance_result": best["compliance_result"] if best else None,
            "confidence": confidence,
            "reason": self._build_reason(best, classification, resolved_page_type),
            "page_type": resolved_page_type,
            "page_confidence": classification.confidence,
        }

    def classify_page(self, db: Session, evidence_id: str, *, ocr_text: str | None = None, extracted_fields: Any = None) -> dict:
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")
        fields = self.field_repository.list_by_evidence(db, evidence_id)
        resolved_text = self._resolve_ocr_text(evidence, ocr_text)
        resolved_fields = extracted_fields if extracted_fields is not None else fields
        if not resolved_text and not resolved_fields:
            raise BadRequestException("EVIDENCE_HISTORY_MATCH_INPUT_NOT_FOUND", "证据缺少 OCR 文本或抽取字段，无法识别页面类型")
        result = self.classifier.classify(resolved_text, resolved_fields)
        return {
            "page_type": result.page_type,
            "confidence": result.confidence,
            "reason": result.reason,
            "matched_keywords": result.matched_keywords,
        }

    def _score_record(self, record: HistoryRecord, ocr_text: str, page_type: str | None, asset_type: str | None, extracted_fields: Any) -> dict:
        score = 0.0
        reasons: list[str] = []
        haystack = self._record_text(record)
        if page_type:
            page_keywords = self.PAGE_TYPE_HISTORY_KEYWORDS.get(page_type, ()) + self.classifier.PAGE_TYPE_KEYWORDS.get(page_type, ())
            page_hits = [keyword for keyword in page_keywords if keyword.lower() in haystack]
            if page_hits:
                score += min(0.35, len(page_hits) * 0.08)
                reasons.append(f"page_type 命中：{'、'.join(page_hits[:5])}")
        if asset_type and record.asset_type == asset_type:
            score += 0.2
            reasons.append("资产类型命中")
        ocr_tokens = self._tokens(ocr_text)
        record_tokens = self._tokens(haystack)
        item_tokens = self._tokens(record.item_text or record.evaluation_item or "")
        record_text_tokens = self._tokens(record.raw_text or record.record_text or "")
        item_overlap = len(ocr_tokens.intersection(item_tokens))
        text_overlap = len(ocr_tokens.intersection(record_text_tokens))
        keyword_overlap = len(ocr_tokens.intersection(set(record.keywords_json or [])))
        if item_overlap:
            score += min(0.2, item_overlap * 0.04)
            reasons.append(f"OCR 与测评项重合 {item_overlap} 个词")
        if text_overlap:
            score += min(0.2, text_overlap * 0.03)
            reasons.append(f"OCR 与结果记录重合 {text_overlap} 个词")
        if keyword_overlap:
            score += min(0.15, keyword_overlap * 0.05)
            reasons.append(f"历史关键词重合 {keyword_overlap} 个")
        field_hits = self._field_hits(extracted_fields, haystack)
        if field_hits:
            score += min(0.1, field_hits * 0.03)
            reasons.append(f"抽取字段命中 {field_hits} 个")
        normalized_score = round(min(score, 0.99), 2)
        return {
            "id": record.id,
            "sheet_name": record.sheet_name,
            "asset_name": record.asset_name,
            "asset_type": record.asset_type,
            "control_point": record.control_point,
            "item_text": record.item_text or record.evaluation_item,
            "evaluation_item": record.evaluation_item,
            "record_text": record.record_text,
            "raw_text": record.raw_text,
            "compliance_result": record.compliance_result or record.compliance_status,
            "compliance_status": record.compliance_status,
            "score": normalized_score,
            "reasons": reasons,
        }

    def _resolve_ocr_text(self, evidence, override: str | None) -> str:
        if override:
            return override
        if evidence.text_content:
            return evidence.text_content
        if isinstance(evidence.ocr_result_json, dict):
            return str(evidence.ocr_result_json.get("full_text") or "")
        return ""

    def _resolve_asset_type(self, evidence) -> str | None:
        if evidence.matched_asset:
            return evidence.matched_asset.category
        reasons = evidence.asset_match_reasons_json if isinstance(evidence.asset_match_reasons_json, dict) else {}
        value = reasons.get("suggested_asset_type") or reasons.get("asset_type")
        return str(value) if value else None

    def _record_text(self, record: HistoryRecord) -> str:
        return " ".join(
            item or ""
            for item in (
                record.asset_type,
                record.control_point,
                record.item_text,
                record.evaluation_item,
                record.raw_text,
                record.record_text,
                record.compliance_result,
                record.compliance_status,
                " ".join(record.keywords_json or []),
            )
        ).lower()

    def _tokens(self, text: str) -> set[str]:
        return {token.lower() for token in self.TOKEN_PATTERN.findall(text or "") if len(token.strip()) >= 2}

    def _field_hits(self, fields: Any, haystack: str) -> int:
        values = self.classifier._flatten(fields)
        return sum(1 for value in values if value and str(value).lower() in haystack)

    def _build_reason(self, best: dict | None, classification, page_type: str | None) -> str:
        if not best:
            return f"页面类型 {page_type or '未识别'} 未匹配到有效历史记录"
        if best["score"] < 0.7:
            return f"最佳候选置信度 {best['score']} 低于 0.7，仅作为人工参考；{'；'.join(best['reasons'])}"
        return f"最佳候选置信度 {best['score']}，可作为优先参考；{'；'.join(best['reasons'])}"
