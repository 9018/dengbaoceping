from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EvidencePageClassificationResult:
    page_type: str | None
    confidence: float
    reason: str
    matched_keywords: list[str]


class EvidencePageClassifier:
    PAGE_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
        "password_policy": ("密码策略", "密码长度", "复杂度", "大写字母", "小写字母", "数字", "特殊字符", "有效期", "口令", "password policy"),
        "login_failure_lock": ("登录失败", "失败次数", "锁定", "超时时间", "非法登录次数", "账户锁定", "lockout"),
        "session_timeout": ("会话超时", "空闲超时", "session timeout", "超时退出", "自动注销"),
        "remote_management_protocol": ("https", "http", "ssh", "telnet", "远程管理", "管理协议"),
        "admin_account": ("管理员", "admin", "root", "超级用户", "管理账户", "账号管理"),
        "user_role_permission": ("角色", "权限", "用户组", "授权", "rbac", "role", "permission"),
        "access_control_policy": ("访问控制", "安全策略", "源地址", "目的地址", "服务", "动作", "命中数", "默认拒绝", "acl", "policy"),
        "security_policy": ("安全策略", "策略配置", "policy", "规则", "安全规则"),
        "intrusion_prevention": ("入侵防御", "入侵检测", "ips", "威胁防护", "攻击防护"),
        "antivirus": ("防病毒", "病毒", "恶意代码", "av", "杀毒", "病毒库"),
        "audit_log": ("审计日志", "操作日志", "audit", "管理员操作", "日志审计"),
        "system_log": ("系统日志", "syslog", "event log", "事件日志", "运行日志"),
        "log_server_config": ("日志服务器", "syslog server", "远程日志", "日志主机", "日志转发"),
        "signature_update": ("特征库", "签名库", "病毒库升级", "signature", "规则库", "升级时间"),
        "system_version": ("系统版本", "版本", "firmware", "version", "build", "软件版本"),
        "ha_status": ("ha", "双机", "主备", "高可用", "冗余", "主节点", "备节点"),
    }
    NORMALIZE_PATTERN = re.compile(r"\s+")

    def classify(self, ocr_text: str | None, extracted_fields: Any = None) -> EvidencePageClassificationResult:
        text = self._build_text(ocr_text, extracted_fields)
        if not text:
            return EvidencePageClassificationResult(None, 0.0, "未提供 OCR 文本或抽取字段，无法识别页面类型", [])
        scored: list[tuple[str, int, list[str]]] = []
        for page_type, keywords in self.PAGE_TYPE_KEYWORDS.items():
            matched = [keyword for keyword in keywords if keyword.lower() in text]
            if matched:
                scored.append((page_type, len(matched), matched))
        if not scored:
            return EvidencePageClassificationResult(None, 0.0, "未命中已知页面类型关键词", [])
        page_type, hit_count, matched_keywords = sorted(scored, key=lambda item: (-item[1], item[0]))[0]
        confidence = min(0.95, 0.35 + hit_count * 0.12)
        reason = f"命中 {page_type} 页面关键词：{'、'.join(matched_keywords[:8])}"
        return EvidencePageClassificationResult(page_type, round(confidence, 2), reason, matched_keywords)

    def _build_text(self, ocr_text: str | None, extracted_fields: Any) -> str:
        parts = [ocr_text or ""]
        parts.extend(self._flatten(extracted_fields))
        return self.NORMALIZE_PATTERN.sub(" ", " ".join(parts)).strip().lower()

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
                return [str(getattr(value, attr) or "")]
        return [str(value)]
