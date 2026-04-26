from __future__ import annotations

from typing import Any
import re

COMPLIANCE_RESULTS = {"符合", "部分符合", "不符合", "不适用", "待人工确认"}
IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
DATE_TIME_PATTERN = re.compile(r"\b\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}(?:日)?(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?\b")
VERSION_PATTERN = re.compile(r"\b[vV]?\d+(?:\.\d+){1,5}\b")


class RecordGenerationService:
    def generate(self, payload) -> dict:
        data = self._to_dict(payload)
        asset_name = self._clean(data.get("asset_name")) or "当前测试对象"
        asset_type = self._clean(data.get("asset_type"))
        page_type = self._clean(data.get("page_type")) or "screenshot"
        matched_item = self._to_dict(data.get("matched_item"))
        facts = self._to_dict(data.get("extracted_facts"))
        history_records = [self._to_dict(item) for item in data.get("similar_history_records") or []]

        if matched_item.get("match_source") == "assessment_template":
            return self._generate_from_assessment_template(asset_name, asset_type, page_type, matched_item, facts, history_records)

        if matched_item.get("match_source") == "project_template" or matched_item.get("record_template"):
            return self._generate_from_project_template(asset_name, asset_type, page_type, matched_item, facts, history_records)

        missing_evidence = self._detect_missing_evidence(page_type, facts)
        self._append_missing_fields(missing_evidence, matched_item.get("missing_fields") or [])
        observation = self._build_observation(asset_type, page_type, facts, missing_evidence)
        fact_sentences = self._build_fact_sentences(asset_name, page_type, facts, matched_item, missing_evidence)
        compliance_result = self._derive_compliance_result(page_type, facts, history_records, missing_evidence)
        evidence_summary = self._build_evidence_summary(facts, matched_item)
        confidence = self._calculate_confidence(asset_name, facts, history_records, missing_evidence, compliance_result)

        record_text = f"经现场核查：{observation}，{fact_sentences}"
        return {
            "record_text": record_text,
            "compliance_result": compliance_result,
            "confidence": confidence,
            "evidence_summary": evidence_summary,
            "missing_evidence": missing_evidence,
        }

    def _generate_from_assessment_template(
        self,
        asset_name: str,
        asset_type: str | None,
        page_type: str,
        matched_item: dict,
        facts: dict,
        history_records: list[dict],
    ) -> dict:
        missing_evidence = self._detect_missing_evidence(page_type, facts)
        self._append_missing_fields(missing_evidence, matched_item.get("missing_fields") or [])
        template_record = self._clean(matched_item.get("record_template"))
        history_sample = self._pick_history_sample(history_records, matched_item, facts)
        if template_record:
            record_text = self._render_assessment_template_record(
                template_record,
                asset_name,
                asset_type,
                page_type,
                matched_item,
                facts,
                history_sample,
                missing_evidence,
            )
        else:
            observation = self._build_observation(asset_type, page_type, facts, missing_evidence)
            fact_sentences = self._build_fact_sentences(asset_name, page_type, facts, matched_item, missing_evidence)
            record_text = f"经现场核查：{observation}，{fact_sentences}"
        compliance_result = self._clean(facts.get("compliance_result") or facts.get("compliance_status"))
        if compliance_result not in COMPLIANCE_RESULTS and missing_evidence:
            compliance_result = "待人工确认"
        if compliance_result not in COMPLIANCE_RESULTS:
            compliance_result = self._clean(matched_item.get("default_compliance"))
        if compliance_result not in COMPLIANCE_RESULTS:
            compliance_result = self._derive_compliance_result(page_type, facts, history_records, missing_evidence)
        evidence_summary = self._build_evidence_summary(facts, matched_item)
        evidence_summary.insert(0, f"模板编号={matched_item.get('item_no') or matched_item.get('item_code') or '-'}")
        if matched_item.get("sheet_name"):
            evidence_summary.insert(1, f"模板Sheet={matched_item['sheet_name']}")
        if history_sample:
            evidence_summary.append(f"历史写法参考={history_sample.get('asset_name') or history_sample.get('id') or '样例'}")
        confidence = self._calculate_template_confidence(facts, history_records, missing_evidence, template_record, compliance_result)
        return {
            "record_text": record_text,
            "compliance_result": compliance_result,
            "confidence": confidence,
            "evidence_summary": evidence_summary[:8],
            "missing_evidence": missing_evidence,
        }

    def _generate_from_project_template(
        self,
        asset_name: str,
        asset_type: str | None,
        page_type: str,
        matched_item: dict,
        facts: dict,
        history_records: list[dict],
    ) -> dict:
        missing_evidence = self._detect_missing_evidence(page_type, facts)
        self._append_missing_fields(missing_evidence, matched_item.get("missing_fields") or [])
        template_record = self._clean(matched_item.get("record_template"))
        if template_record:
            record_text = template_record
        else:
            observation = self._build_observation(asset_type, page_type, facts, missing_evidence)
            fact_sentences = self._build_fact_sentences(asset_name, page_type, facts, matched_item, missing_evidence)
            record_text = f"经现场核查：{observation}，{fact_sentences}"
        compliance_result = self._clean(facts.get("compliance_result") or facts.get("compliance_status"))
        if compliance_result not in COMPLIANCE_RESULTS:
            compliance_result = self._clean(matched_item.get("default_compliance"))
        if compliance_result not in COMPLIANCE_RESULTS:
            compliance_result = self._derive_compliance_result(page_type, facts, history_records, missing_evidence)
        evidence_summary = self._build_evidence_summary(facts, matched_item)
        evidence_summary.insert(0, f"模板编号={matched_item.get('item_no') or matched_item.get('item_code') or '-'}")
        if matched_item.get("sheet_name"):
            evidence_summary.insert(1, f"模板Sheet={matched_item['sheet_name']}")
        confidence = self._calculate_template_confidence(facts, history_records, missing_evidence, template_record, compliance_result)
        return {
            "record_text": record_text,
            "compliance_result": compliance_result,
            "confidence": confidence,
            "evidence_summary": evidence_summary[:8],
            "missing_evidence": missing_evidence,
        }

    def _build_observation(self, asset_type: str | None, page_type: str, facts: dict, missing_evidence: list[str]) -> str:
        command = self._clean(facts.get("command"))
        page_name = self._clean(facts.get("page_name")) or self._default_page_name(page_type)
        if command or page_type in {"cli", "terminal", "command"}:
            if command:
                return f"通过执行 {command} 命令"
            self._append_missing(missing_evidence, "执行命令")
            return "通过命令行截图"
        if self._is_firewall(asset_type) or page_type in {"password_policy", "access_control_policy", "login_failure_lock", "remote_management_protocol"}:
            if page_name:
                return f"查看系统-{page_name}页面"
            self._append_missing(missing_evidence, "系统页面名称")
        return "查看相关证据截图"

    def _build_fact_sentences(self, asset_name: str, page_type: str, facts: dict, matched_item: dict, missing_evidence: list[str]) -> str:
        if page_type == "password_policy":
            return self._build_password_policy_text(asset_name, facts, missing_evidence)
        parts = [f"{asset_name}相关配置情况如下"]
        for key, value in facts.items():
            if key in {"asset_name", "asset_type", "page_type", "page_name", "command", "ocr_text_available", "evidence_title", "source_ref"}:
                continue
            normalized = self._format_fact_value(value)
            if normalized:
                parts.append(f"{self._fact_label(key)}为{normalized}")
        if len(parts) == 1:
            level3 = self._clean(matched_item.get("level3")) or self._clean(matched_item.get("section_title")) or "当前测评项"
            self._append_missing(missing_evidence, "可用于判定的截图事实")
            parts.append(f"截图中未体现{level3}的关键配置值")
        return "；".join(parts) + "。"

    def _build_password_policy_text(self, asset_name: str, facts: dict, missing_evidence: list[str]) -> str:
        parts = [f"1、{asset_name}已启用身份鉴别功能，用户通过账户名和口令登录设备进行管理"]
        policy_parts: list[str] = []
        min_length = self._clean(facts.get("password_min_length"))
        complexity = self._clean(facts.get("complexity") or facts.get("password_complexity"))
        expire_days = facts.get("password_expire_days")
        if min_length:
            policy_parts.append(f"密码长度大于等于{min_length}位")
        else:
            self._append_missing(missing_evidence, "密码最小长度")
        if complexity:
            policy_parts.append(f"必须包含{complexity}")
        else:
            self._append_missing(missing_evidence, "密码复杂度要求")
        if expire_days is None or expire_days == "" or str(expire_days).lower() == "null":
            policy_parts.append("口令未设置有效期")
        else:
            policy_parts.append(f"口令有效期为{expire_days}天")
        if policy_parts:
            parts.append(f"2、设备提供口令复杂度校验功能，当前密码策略如下：{'，'.join(policy_parts)}")
        return "；".join(parts) + "。"

    def _derive_compliance_result(self, page_type: str, facts: dict, history_records: list[dict], missing_evidence: list[str]) -> str:
        explicit = self._clean(facts.get("compliance_result") or facts.get("compliance_status"))
        if explicit in COMPLIANCE_RESULTS:
            return explicit
        if missing_evidence:
            return "待人工确认"
        if page_type == "password_policy":
            expire_days = facts.get("password_expire_days")
            if expire_days is None or expire_days == "" or str(expire_days).lower() == "null":
                return "部分符合"
            return "符合"
        best_history = next((item for item in history_records if self._clean(item.get("compliance_result") or item.get("compliance_status")) in COMPLIANCE_RESULTS), None)
        if best_history:
            return self._clean(best_history.get("compliance_result") or best_history.get("compliance_status"))
        return "待人工确认"

    def _detect_missing_evidence(self, page_type: str, facts: dict) -> list[str]:
        missing: list[str] = []
        if page_type == "password_policy":
            if not self._clean(facts.get("password_min_length")):
                missing.append("密码最小长度")
            if not self._clean(facts.get("complexity") or facts.get("password_complexity")):
                missing.append("密码复杂度要求")
        return missing

    def _append_missing_fields(self, missing_evidence: list[str], missing_fields: list[str]) -> None:
        for field in missing_fields:
            label = self._fact_label(str(field))
            self._append_missing(missing_evidence, label)

    def _build_evidence_summary(self, facts: dict, matched_item: dict) -> list[str]:
        summary: list[str] = []
        title = self._clean(matched_item.get("section_title") or matched_item.get("level3"))
        if title:
            summary.append(f"命中测评项：{title}")
        for key, value in facts.items():
            if key in {"ocr_text_available", "evidence_title", "source_ref"}:
                continue
            normalized = self._format_fact_value(value)
            if normalized:
                summary.append(f"{self._fact_label(key)}={normalized}")
        return summary[:8]

    def _calculate_confidence(self, asset_name: str, facts: dict, history_records: list[dict], missing_evidence: list[str], compliance_result: str) -> float:
        score = 0.4
        if asset_name:
            score += 0.1
        fact_count = len([value for value in facts.values() if self._format_fact_value(value)])
        if fact_count:
            score += min(0.2, fact_count * 0.04)
        if self._clean(facts.get("page_name")) or self._clean(facts.get("command")):
            score += 0.1
        if history_records:
            score += 0.1
        if compliance_result != "待人工确认":
            score += 0.1
        score -= min(0.3, len(missing_evidence) * 0.1)
        if missing_evidence:
            score = min(score, 0.6)
        return round(max(0.0, min(score, 1.0)), 2)

    def _calculate_template_confidence(
        self,
        facts: dict,
        history_records: list[dict],
        missing_evidence: list[str],
        template_record: str | None,
        compliance_result: str,
    ) -> float:
        score = 0.65
        if template_record:
            score += 0.1
        fact_count = len([value for value in facts.values() if self._format_fact_value(value)])
        if fact_count:
            score += min(0.12, fact_count * 0.02)
        if history_records:
            score += 0.05
        if compliance_result and compliance_result != "待人工确认":
            score += 0.05
        score -= min(0.2, len(missing_evidence) * 0.08)
        if missing_evidence:
            score = min(score, 0.68)
        return round(max(0.0, min(score, 1.0)), 2)

    def _render_assessment_template_record(
        self,
        template_record: str,
        asset_name: str,
        asset_type: str | None,
        page_type: str,
        matched_item: dict,
        facts: dict,
        history_sample: dict | None,
        missing_evidence: list[str],
    ) -> str:
        rendered = template_record
        rendered = self._replace_template_placeholders(rendered, asset_name, asset_type, page_type, matched_item, facts)
        rendered = self._rewrite_with_fact_values(rendered, facts)
        rendered = self._strip_history_specifics(rendered, history_sample, asset_name, facts)
        rendered = self._append_missing_template_facts(rendered, asset_name, page_type, facts, matched_item, missing_evidence)
        return self._normalize_record_text(rendered)

    def _pick_history_sample(self, history_records: list[dict], matched_item: dict, facts: dict) -> dict | None:
        if not history_records:
            return None
        expected = self._clean(facts.get("compliance_result") or facts.get("compliance_status") or matched_item.get("default_compliance"))
        if expected:
            for item in history_records:
                compliance = self._clean(item.get("compliance_result") or item.get("compliance_status"))
                if compliance == expected:
                    return item
        return history_records[0]

    def _replace_template_placeholders(
        self,
        text: str,
        asset_name: str,
        asset_type: str | None,
        page_type: str,
        matched_item: dict,
        facts: dict,
    ) -> str:
        replacements = {
            "{资产名称}": asset_name,
            "{{资产名称}}": asset_name,
            "[资产名称]": asset_name,
            "{测试对象}": asset_name,
            "{{测试对象}}": asset_name,
            "[测试对象]": asset_name,
            "{对象名称}": asset_name,
            "{对象类型}": asset_type or matched_item.get("asset_type") or "测试对象",
            "{页面名称}": self._clean(facts.get("page_name")) or self._default_page_name(page_type) or "相关页面",
            "{控制点}": self._clean(matched_item.get("control_point")) or self._clean(matched_item.get("level2")) or "当前控制点",
            "{测评项}": self._clean(matched_item.get("level3")) or self._clean(matched_item.get("section_title")) or "当前测评项",
            "{命令}": self._clean(facts.get("command")) or "相关命令",
        }
        rendered = text
        for source, target in replacements.items():
            rendered = rendered.replace(source, str(target))
        return rendered

    def _rewrite_with_fact_values(self, text: str, facts: dict) -> str:
        replacements = [
            (["password_min_length"], lambda value: f"密码长度大于等于{value}位"),
            (["complexity", "password_complexity"], lambda value: f"密码复杂度要求为{value}"),
            (["password_expire_days"], self._format_password_expire_sentence),
            (["remote_login_status", "remote_login_allowed"], lambda value: f"远程登录状态为{value}"),
            (["log_retention_days"], lambda value: f"日志保留时间为{value}天"),
            (["signature_version", "virus_database_version"], lambda value: f"病毒库版本为{value}"),
            (["asset_ip", "device_ip", "ip"], lambda value: f"IP地址为{value}"),
            (["asset_version", "version"], lambda value: f"版本为{value}"),
            (["check_time", "time", "timestamp"], lambda value: f"时间为{value}"),
        ]
        rendered = text
        for keys, formatter in replacements:
            value = None
            for key in keys:
                value = self._format_fact_value(facts.get(key))
                if value:
                    break
            if not value:
                continue
            rendered = self._replace_sentence_containing_any(rendered, [self._fact_label(key) for key in keys] + [formatter(value)], formatter(value))
        return rendered

    def _format_password_expire_sentence(self, value: str) -> str:
        if value in {"未设置", "none", "None"}:
            return "口令未设置有效期"
        return f"口令有效期为{value}天"

    def _strip_history_specifics(self, text: str, history_sample: dict | None, asset_name: str, facts: dict) -> str:
        rendered = text
        current_ip = self._format_fact_value(facts.get("asset_ip") or facts.get("device_ip") or facts.get("ip")) or "当前IP"
        current_version = self._format_fact_value(facts.get("asset_version") or facts.get("version")) or "当前版本"
        current_time = self._format_fact_value(facts.get("check_time") or facts.get("time") or facts.get("timestamp")) or "当前时间"
        if history_sample:
            old_asset_name = self._clean(history_sample.get("asset_name"))
            if old_asset_name:
                rendered = rendered.replace(old_asset_name, asset_name)
            old_ip = self._clean(history_sample.get("asset_ip"))
            if old_ip:
                rendered = rendered.replace(old_ip, current_ip)
            old_version = self._clean(history_sample.get("asset_version"))
            if old_version:
                rendered = rendered.replace(old_version, current_version)
        rendered = DATE_TIME_PATTERN.sub(current_time, rendered)
        rendered = IP_PATTERN.sub(lambda match: match.group(0) if self._looks_like_placeholder_context(rendered, match.start()) else current_ip, rendered)
        return rendered

    def _replace_version_token(self, match: re.Match[str], current_version: str) -> str:
        token = match.group(0)
        if token.isdigit():
            return token
        return current_version

    def _looks_like_placeholder_context(self, text: str, index: int) -> bool:
        start = max(0, index - 8)
        context = text[start:index]
        return any(token in context for token in ("IP", "ip", "地址", "主机"))

    def _append_missing_template_facts(
        self,
        text: str,
        asset_name: str,
        page_type: str,
        facts: dict,
        matched_item: dict,
        missing_evidence: list[str],
    ) -> str:
        if not missing_evidence:
            return text
        if text.endswith("。"):
            base = text[:-1]
        else:
            base = text
        missing_clause = f"；当前截图尚未体现{'、'.join(missing_evidence)}"
        if page_type == "password_policy" and "口令未设置有效期" not in base and facts.get("password_expire_days") in {None, "", "null", "None"}:
            base = f"{base}；口令未设置有效期"
        if asset_name not in base:
            base = f"{asset_name}{base if base.startswith('已') else '：' + base}"
        return f"{base}{missing_clause}。"

    def _replace_sentence_containing_any(self, text: str, candidates: list[str], replacement: str) -> str:
        segments = re.split(r"(?<=[；。])", text)
        updated = False
        normalized_candidates = [candidate for candidate in candidates if candidate]
        for index, segment in enumerate(segments):
            compact = re.sub(r"\s+", "", segment)
            if any(re.sub(r"\s+", "", candidate) in compact for candidate in normalized_candidates):
                suffix = "" if segment.endswith(("；", "。")) else ""
                segments[index] = replacement + ("。" if segment.endswith("。") else "；" if segment.endswith("；") else suffix)
                updated = True
        if updated:
            return "".join(segments)
        if text and not text.endswith(("；", "。")):
            return f"{text}；{replacement}"
        joiner = "" if not text else ""
        return f"{text}{joiner}{replacement}"

    def _normalize_record_text(self, text: str) -> str:
        normalized = re.sub(r"[；]{2,}", "；", text)
        normalized = re.sub(r"[。]{2,}", "。", normalized)
        normalized = re.sub(r"；。", "。", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if not normalized.endswith("。"):
            normalized = f"{normalized}。"
        return normalized

    def _default_page_name(self, page_type: str) -> str | None:
        return {
            "password_policy": "管理员账号-密码安全策略",
            "login_failure_lock": "管理员账号-登录失败锁定策略",
            "access_control_policy": "安全策略",
            "remote_management_protocol": "管理协议配置",
        }.get(page_type)

    def _is_firewall(self, asset_type: str | None) -> bool:
        value = (asset_type or "").lower()
        return any(token in value for token in ("firewall", "防火墙", "安全设备"))

    def _fact_label(self, key: str) -> str:
        return {
            "password_min_length": "密码最小长度",
            "complexity": "密码复杂度",
            "password_complexity": "密码复杂度",
            "password_expire_days": "口令有效期",
            "remote_login_status": "远程登录状态",
            "remote_login_allowed": "远程登录状态",
            "admin_account_count": "管理员账户数量",
            "log_retention_days": "日志保留时间",
            "antivirus_status": "防病毒软件安装状态",
            "antivirus_installed": "防病毒软件安装状态",
            "signature_version": "病毒库版本",
            "virus_database_version": "病毒库版本",
            "action": "动作",
        }.get(key, key)

    def _format_fact_value(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return "是" if value else "否"
        if isinstance(value, (list, tuple, set)):
            items = [self._format_fact_value(item) for item in value]
            return "、".join(item for item in items if item)
        if isinstance(value, dict):
            return None
        text = str(value).strip()
        if not text or text.lower() == "null":
            return None
        return text

    def _append_missing(self, missing_evidence: list[str], item: str) -> None:
        if item not in missing_evidence:
            missing_evidence.append(item)

    def _clean(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _to_dict(self, value: Any) -> dict:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump()
        return {key: getattr(value, key) for key in dir(value) if not key.startswith("_") and not callable(getattr(value, key))}
