from app.services.evidence_page_classifier import EvidencePageClassifier


def test_classify_password_policy():
    result = EvidencePageClassifier().classify("密码策略 密码长度 复杂度 大写字母 小写字母 数字 特殊字符 有效期")

    assert result.page_type == "password_policy"
    assert result.confidence >= 0.7
    assert "密码策略" in result.matched_keywords


def test_classify_login_failure_lock():
    result = EvidencePageClassifier().classify("登录失败 锁定 超时时间 非法登录次数")

    assert result.page_type == "login_failure_lock"
    assert result.confidence >= 0.7


def test_classify_remote_management_protocol():
    result = EvidencePageClassifier().classify("系统启用 HTTPS HTTP SSH Telnet 远程管理协议")

    assert result.page_type == "remote_management_protocol"
    assert result.confidence >= 0.7


def test_classify_access_control_policy():
    result = EvidencePageClassifier().classify("安全策略 源地址 目的地址 服务 动作 命中数 默认拒绝")

    assert result.page_type == "access_control_policy"
    assert result.confidence >= 0.7


def test_classify_empty_text_low_confidence():
    result = EvidencePageClassifier().classify("")

    assert result.page_type is None
    assert result.confidence == 0.0
    assert result.reason
