from app.services.record_generation_service import RecordGenerationService


def test_generate_password_policy_record_matches_required_style():
    result = RecordGenerationService().generate(
        {
            "asset_name": "出口防火墙-A",
            "asset_type": "安全设备",
            "page_type": "password_policy",
            "matched_item": {"section_title": "身份鉴别"},
            "extracted_facts": {
                "password_min_length": 8,
                "complexity": "大小写字母、数字、特殊字符任意三种",
                "password_expire_days": None,
            },
            "similar_history_records": [
                {
                    "asset_name": "旧防火墙",
                    "record_text": "经现场核查，旧防火墙密码长度为12位。",
                    "compliance_result": "符合",
                }
            ],
        }
    )

    assert result["record_text"].startswith("经现场核查：")
    assert "出口防火墙-A" in result["record_text"]
    assert "旧防火墙" not in result["record_text"]
    assert "查看系统-管理员账号-密码安全策略页面" in result["record_text"]
    assert "密码长度大于等于8位" in result["record_text"]
    assert "必须包含大小写字母、数字、特殊字符任意三种" in result["record_text"]
    assert "口令未设置有效期" in result["record_text"]
    assert "12" not in result["record_text"]
    assert result["compliance_result"] == "部分符合"
    assert result["confidence"] >= 0.7
    assert result["missing_evidence"] == []


def test_generate_cli_record_uses_command_wording():
    result = RecordGenerationService().generate(
        {
            "asset_name": "核心交换机-A",
            "asset_type": "switch",
            "page_type": "cli",
            "matched_item": {"level3": "访问控制"},
            "extracted_facts": {"command": "show running-config", "remote_login_status": "enabled"},
            "similar_history_records": [],
        }
    )

    assert "通过执行 show running-config 命令" in result["record_text"]
    assert "核心交换机-A" in result["record_text"]
    assert "远程登录状态为enabled" in result["record_text"]


def test_missing_key_facts_returns_missing_evidence_and_conservative_result():
    result = RecordGenerationService().generate(
        {
            "asset_name": "出口防火墙-A",
            "asset_type": "firewall",
            "page_type": "password_policy",
            "matched_item": {"section_title": "身份鉴别"},
            "extracted_facts": {"password_expire_days": None},
            "similar_history_records": [],
        }
    )

    assert "密码最小长度" in result["missing_evidence"]
    assert "密码复杂度要求" in result["missing_evidence"]
    assert result["compliance_result"] == "待人工确认"
    assert result["confidence"] <= 0.6


def test_history_specific_values_are_not_copied_without_facts():
    result = RecordGenerationService().generate(
        {
            "asset_name": "日志审计-A",
            "asset_type": "audit",
            "page_type": "system_log",
            "matched_item": {"level3": "日志留存"},
            "extracted_facts": {"page_name": "日志配置"},
            "similar_history_records": [
                {
                    "asset_name": "旧日志审计",
                    "record_text": "经现场核查，旧日志审计日志保留180天。",
                    "compliance_result": "符合",
                }
            ],
        }
    )

    assert "旧日志审计" not in result["record_text"]
    assert "180" not in result["record_text"]
    assert result["record_text"].startswith("经现场核查：")
