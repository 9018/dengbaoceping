from types import SimpleNamespace

import pytest
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException
from app.schemas.evidence import EvidenceUploadData
from app.services.evidence_service import EvidenceService
from app.services.export_service import ExportService
from app.services.field_extraction_service import FieldExtractionService
from app.services.project_service import ProjectService
from app.services.record_service import RecordService


def create_project(service: ProjectService, db: Session, code: str = "PJT-SVC"):
    payload = SimpleNamespace(
        code=code,
        name="服务测试项目",
        project_type="等级保护测评",
        status="draft",
        description=None,
        model_dump=lambda: {
            "code": code,
            "name": "服务测试项目",
            "project_type": "等级保护测评",
            "status": "draft",
            "description": None,
        },
    )
    return service.create_project(db, payload=payload)


def upload_evidence(service: EvidenceService, db: Session, project_id: str, filename: str = "sample.txt"):
    with open(__file__, "rb") as fh:
        upload = UploadFile(filename=filename, file=fh)
        payload = EvidenceUploadData(title="样例证据", evidence_type="screenshot", summary="服务测试", device="FW-01")
        return service.upload_project_evidence(db, project_id, upload, payload)


def test_field_extraction_service_requires_ocr_text(db_session):
    project_service = ProjectService()
    evidence_service = EvidenceService()
    field_service = FieldExtractionService()

    project = create_project(project_service, db_session)
    evidence = upload_evidence(evidence_service, db_session, project.id)

    with pytest.raises(BadRequestException) as exc:
        field_service.extract_fields(db_session, evidence.id, "security_device_basic")
    assert exc.value.code == "OCR_TEXT_NOT_FOUND"


def test_record_service_reuses_existing_record_without_force(db_session):
    project_service = ProjectService()
    evidence_service = EvidenceService()
    field_service = FieldExtractionService()
    record_service = RecordService()

    project = create_project(project_service, db_session, code="PJT-REC-SVC")
    evidence = upload_evidence(evidence_service, db_session, project.id)
    evidence.text_content = "设备名称: FW-01\n设备IP: 10.0.0.1\n安全策略状态: 已启用\n"
    db_session.commit()
    field_service.extract_fields(db_session, evidence.id, "security_device_basic")

    first = record_service.generate_record(db_session, project.id, evidence.id)
    second = record_service.generate_record(db_session, project.id, evidence.id)
    assert first.id == second.id


def extracted_by_code(fields):
    return {field.rule_id: field for field in fields}


def test_field_extraction_service_extracts_windows_password_policy(db_session):
    project_service = ProjectService()
    evidence_service = EvidenceService()
    field_service = FieldExtractionService()

    project = create_project(project_service, db_session, code="PJT-WIN-POLICY")
    evidence = upload_evidence(evidence_service, db_session, project.id, filename="windows-policy.txt")
    evidence.text_content = """
最小密码长度：I2 位
密码复杂度 = 大写字母、小写字母、数字和特殊字符
密码最长使用期限：9O天
账户锁定阈值 = 5次
账户锁定时间：3O 分钟
登录失败处理：锁定
默认账户状态：禁用
""".strip()
    db_session.commit()

    fields = extracted_by_code(field_service.extract_fields(db_session, evidence.id))

    assert fields["password_min_length"].corrected_value == "12"
    assert fields["password_min_length"].field_value_number == 12.0
    assert fields["password_complexity"].corrected_value == "upper+lower+digit+special"
    assert fields["password_max_age"].corrected_value == "90"
    assert fields["password_max_age"].field_value_number == 90.0
    assert fields["account_lockout_threshold"].corrected_value == "5"
    assert fields["account_lockout_duration"].corrected_value == "30"
    assert fields["login_failure_action"].corrected_value == "lock"
    assert fields["default_account_status"].corrected_value == "disabled"


def test_field_extraction_service_extracts_linux_ssh_config(db_session):
    project_service = ProjectService()
    evidence_service = EvidenceService()
    field_service = FieldExtractionService()

    project = create_project(project_service, db_session, code="PJT-LINUX-SSH")
    evidence = upload_evidence(evidence_service, db_session, project.id, filename="linux-ssh.txt")
    evidence.text_content = """
PermitRootLogin = yes
是否允许远程登录：是
RDP：关闭
管理员账户数量 = 2个
长期未用账户状态：禁用
""".strip()
    db_session.commit()

    fields = extracted_by_code(field_service.extract_fields(db_session, evidence.id))

    assert fields["ssh_root_login"].corrected_value == "enabled"
    assert fields["ssh_root_login"].field_value_bool is True
    assert fields["remote_login_allowed"].corrected_value == "enabled"
    assert fields["remote_login_allowed"].field_value_bool is True
    assert fields["rdp_enabled"].corrected_value == "disabled"
    assert fields["rdp_enabled"].field_value_bool is False
    assert fields["admin_account_count"].corrected_value == "2"
    assert fields["admin_account_count"].field_value_number == 2.0
    assert fields["unused_account_status"].corrected_value == "disabled"


def test_field_extraction_service_extracts_firewall_policy_fields(db_session):
    project_service = ProjectService()
    evidence_service = EvidenceService()
    field_service = FieldExtractionService()

    project = create_project(project_service, db_session, code="PJT-FW-POLICY")
    evidence = upload_evidence(evidence_service, db_session, project.id, filename="firewall-policy.txt")
    evidence.text_content = """
防火墙策略名称：互联网访问控制
访问控制策略名称 = 办公网访问DMZ
源区域：Trust
目的区域 = DMZ
源地址：10.O.0.0/24
目的地址：172.16.I.10
服务端口：22, 443
NAT状态：开启
默认拒绝策略：是
安全域：DMZ
""".strip()
    db_session.commit()

    fields = extracted_by_code(field_service.extract_fields(db_session, evidence.id))

    assert fields["firewall_policy_name"].corrected_value == "互联网访问控制"
    assert fields["access_policy_name"].corrected_value == "办公网访问DMZ"
    assert fields["source_zone"].corrected_value == "Trust"
    assert fields["destination_zone"].corrected_value == "DMZ"
    assert fields["source_address"].corrected_value == "10.0.0.0/24"
    assert fields["destination_address"].corrected_value == "172.16.1.10"
    assert fields["service_port"].corrected_value == "22, 443"
    assert fields["nat_enabled"].corrected_value == "enabled"
    assert fields["nat_enabled"].field_value_bool is True
    assert fields["deny_all_policy"].corrected_value == "enabled"
    assert fields["deny_all_policy"].field_value_bool is True
    assert fields["security_zone"].corrected_value == "DMZ"


def test_field_extraction_service_extracts_audit_configuration(db_session):
    project_service = ProjectService()
    evidence_service = EvidenceService()
    field_service = FieldExtractionService()

    project = create_project(project_service, db_session, code="PJT-AUDIT")
    evidence = upload_evidence(evidence_service, db_session, project.id, filename="audit-config.txt")
    evidence.text_content = """
审计功能状态：已启用
登录日志 = 开启
操作日志：enabled
日志保留时间：18O 天
Syslog服务器：10.O.0.5
NTP服务器 = 192.168.O.10
时间同步状态：是
""".strip()
    db_session.commit()

    fields = extracted_by_code(field_service.extract_fields(db_session, evidence.id))

    assert fields["audit_enabled"].corrected_value == "enabled"
    assert fields["audit_enabled"].field_value_bool is True
    assert fields["login_log_enabled"].corrected_value == "enabled"
    assert fields["operation_log_enabled"].corrected_value == "enabled"
    assert fields["log_retention_days"].corrected_value == "180"
    assert fields["log_retention_days"].field_value_number == 180.0
    assert fields["syslog_server"].corrected_value == "10.0.0.5"
    assert fields["ntp_server"].corrected_value == "192.168.0.10"
    assert fields["time_sync_enabled"].corrected_value == "enabled"
    assert fields["time_sync_enabled"].field_value_bool is True


def test_field_extraction_service_extracts_antivirus_and_protection_fields(db_session):
    project_service = ProjectService()
    evidence_service = EvidenceService()
    field_service = FieldExtractionService()

    project = create_project(project_service, db_session, code="PJT-AV")
    evidence = upload_evidence(evidence_service, db_session, project.id, filename="antivirus-config.txt")
    evidence.text_content = """
补丁状态：最新
非必要服务状态：禁用
高危端口：3389
弱口令检查：开启
基线检查状态：已启用
已安装杀毒软件：是
实时防护状态：启用
病毒库版本 = V1.2.3
最近扫描时间：2026-04-25 O8:3O
""".strip()
    db_session.commit()

    fields = extracted_by_code(field_service.extract_fields(db_session, evidence.id))

    assert fields["patch_status"].corrected_value == "up_to_date"
    assert fields["unnecessary_service_status"].corrected_value == "disabled"
    assert fields["high_risk_port"].corrected_value == "3389"
    assert fields["weak_password_check"].corrected_value == "enabled"
    assert fields["weak_password_check"].field_value_bool is True
    assert fields["baseline_check_status"].corrected_value == "enabled"
    assert fields["antivirus_installed"].corrected_value == "enabled"
    assert fields["antivirus_installed"].field_value_bool is True
    assert fields["realtime_protection_enabled"].corrected_value == "enabled"
    assert fields["realtime_protection_enabled"].field_value_bool is True
    assert fields["virus_database_version"].corrected_value == "V1.2.3"
    assert fields["last_scan_time"].corrected_value == "2026-04-25 08:30"


def test_record_service_rejects_invalid_status_transition(db_session):
    record_service = RecordService()
    with pytest.raises(BadRequestException) as exc:
        record_service._validate_transition("reviewed", "exported")
    assert exc.value.code == "INVALID_RECORD_STATUS_TRANSITION"


def test_export_service_renders_empty_project_group(db_session):
    export_service = ExportService()
    content = export_service._render_txt("空项目", [])
    assert "项目：空项目" in content
    assert "设备：未分组" in content
    assert "无测评记录" in content
