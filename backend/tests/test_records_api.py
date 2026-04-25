from pathlib import Path

from app.core.config import settings


def create_project(client):
    resp = client.post(
        "/api/v1/projects",
        json={"code": "PJT-REC", "name": "记录项目", "project_type": "等级保护测评", "status": "draft"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def upload_evidence(client, project_id: str, filename: str) -> str:
    upload_resp = client.post(
        f"/api/v1/projects/{project_id}/evidences/upload",
        files={"file": (filename, b"hello evidence", "text/plain")},
        data={
            "title": "配置截图",
            "evidence_type": "screenshot",
            "summary": "记录生成",
            "device": "AUTO",
            "tags_json": '["record"]',
            "source_ref": "test-upload",
        },
    )
    assert upload_resp.status_code == 201
    return upload_resp.json()["data"]["id"]


def run_extract_flow(client, evidence_id: str, sample_id: str, template_code: str):
    ocr_resp = client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": sample_id})
    assert ocr_resp.status_code == 200
    extract_resp = client.post(
        f"/api/v1/evidences/{evidence_id}/extract-fields",
        json={"template_code": template_code},
    )
    assert extract_resp.status_code == 200
    return extract_resp.json()


def test_generate_record_full_match(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")
    run_extract_flow(client, evidence_id, "firewall_basic", "security_device_basic")

    from tests.test_guidance_api import import_network_guidance, import_sample_history
    from pathlib import Path
    import tempfile

    tmp_path = Path(tempfile.mkdtemp())
    guidance_resp = import_network_guidance(client, tmp_path)
    history_resp = import_sample_history(client)
    assert guidance_resp.status_code == 201
    assert history_resp.status_code == 201
    guidance_match_resp = client.post(f"/api/v1/evidences/{evidence_id}/match-guidance", json={"force": True})
    assert guidance_match_resp.status_code == 200
    assert guidance_match_resp.json()["data"]["matched_guidance"]["section_title"] == "边界防护"

    resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={"evidence_id": evidence_id},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["message"] == "测评记录生成成功"
    data = body["data"]
    assert data["item_code"] == "net_boundary_firewall_config"
    assert data["template_code"] == "security_device_basic"
    assert data["status"] == "generated"
    assert data["match_score"] >= 0.6
    assert "FW-01" in data["title"]
    assert "待补充" not in data["record_content"]
    assert len(data["matched_fields_json"]) == 3

    rerun_resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={"evidence_id": evidence_id, "force_regenerate": True},
    )
    assert rerun_resp.status_code == 201
    rerun_data = rerun_resp.json()["data"]
    assert rerun_data["id"] != data["id"]

    list_resp = client.get(f"/api/v1/projects/{project_id}/records")
    assert list_resp.status_code == 200
    assert list_resp.json()["meta"]["total"] == 1

    detail_resp = client.get(f"/api/v1/records/{rerun_data['id']}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["data"]["evidence_ids"] == [evidence_id]


def test_generate_record_with_missing_field_fallback(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "policy_missing_action.txt")
    run_extract_flow(client, evidence_id, "security_policy_missing_action", "security_policy_basic")

    resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={"evidence_id": evidence_id},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["item_code"] == "security_policy_check"
    assert data["status"] == "reviewed"
    assert "[待补充: action]" in data["record_content"]
    assert "缺失字段: action" in data["review_comment"]
    assert data["match_score"] < 0.7
    assert "缺失字段: action" in data["match_reasons"]["summary"]


def test_generate_record_with_low_score_override_device_type(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "windows_host_partial.txt")
    run_extract_flow(client, evidence_id, "windows_host_partial", "host_basic_info")

    resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={"evidence_id": evidence_id, "device_type_override": "firewall"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["item_code"] == "host_basic_info_check"
    assert data["status"] == "reviewed"
    assert data["match_score"] < 0.65
    assert "匹配得分低于阈值" in data["review_comment"]
    assert data["match_reasons"]["device_type_reason"].startswith("设备类型冲突")


def test_generate_record_low_confidence_without_missing_fields(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "host-malware-low-confidence.txt")
    run_extract_flow(client, evidence_id, "host_malware_protection", "host_malware_protection")

    resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={
            "evidence_id": evidence_id,
            "selected_item_code": "malware_antivirus_check",
        },
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["item_code"] == "malware_antivirus_check"
    assert data["status"] == "generated_low_confidence"
    assert data["match_score"] < 0.7
    assert "匹配得分低于阈值" in data["review_comment"]
    assert data["match_reasons"]["missing_required_fields"] == []
    assert data["match_reasons"]["selection_mode"] == "manual_item"


def test_generate_record_password_policy_match(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "windows-password-policy.txt")
    run_extract_flow(client, evidence_id, "windows_password_policy", "host_password_policy")

    resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={"evidence_id": evidence_id},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["item_code"] == "host_password_policy_check"
    assert data["template_code"] == "host_password_policy"
    assert data["status"] == "generated"
    assert "WIN-SRV-01" in data["title"]
    assert "最小密码长度为12" in data["record_content"]
    assert data["match_score"] >= 0.7
    assert len(data["matched_fields_json"]) == 4


def test_generate_record_access_control_match(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "linux-access-control.txt")
    run_extract_flow(client, evidence_id, "linux_access_control", "host_access_control")

    resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={"evidence_id": evidence_id},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["item_code"] == "host_access_control_check"
    assert data["template_code"] == "host_access_control"
    assert data["status"] == "generated"
    assert "SRV-LINUX-01" in data["title"]
    assert "远程登录状态为enabled" in data["record_content"]
    assert "管理员账户数量为2" in data["record_content"]
    assert data["match_score"] >= 0.65
    assert len(data["matched_fields_json"]) == 4


def test_generate_record_audit_config_match(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "host-audit-config.txt")
    run_extract_flow(client, evidence_id, "host_audit_config", "host_audit_config")

    resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={"evidence_id": evidence_id},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["item_code"] == "host_audit_config_check"
    assert data["template_code"] == "host_audit_config"
    assert data["status"] == "generated"
    assert "SRV-AUDIT-01" in data["title"]
    assert "日志保留时间为180天" in data["record_content"]
    assert data["match_score"] >= 0.7
    assert len(data["matched_fields_json"]) == 4


def test_generate_record_malware_protection_match(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "host-malware-protection.txt")
    run_extract_flow(client, evidence_id, "host_malware_protection", "host_malware_protection")

    resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={"evidence_id": evidence_id},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["item_code"] == "host_malware_protection_check"
    assert data["template_code"] == "host_malware_protection"
    assert data["status"] == "generated"
    assert "SRV-AV-01" in data["title"]
    assert "防病毒软件安装状态为enabled" in data["record_content"]
    assert "病毒库版本为V1.2.3" in data["record_content"]
    assert data["match_score"] >= 0.7
    assert len(data["matched_fields_json"]) == 4


def test_generate_record_returns_top_candidates_sorted(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "windows-password-policy-ranking.txt")
    run_extract_flow(client, evidence_id, "windows_password_policy", "host_password_policy")

    resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={"evidence_id": evidence_id},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    candidates = data["match_candidates"]
    assert len(candidates) == 3
    assert candidates[0]["item_code"] == "host_password_policy_check"
    assert candidates[0]["score"] >= candidates[1]["score"] >= candidates[2]["score"]
    assert candidates[1]["item_code"] in {"identity_password_policy_check", "identity_account_lockout_check"}
    assert "命中 required field: password_min_length" in candidates[0]["reasons"]["summary"]


def test_generate_record_supports_manual_candidate_selection(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "windows-password-policy-manual.txt")
    run_extract_flow(client, evidence_id, "windows_password_policy", "host_password_policy")

    auto_resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={"evidence_id": evidence_id},
    )
    assert auto_resp.status_code == 201
    auto_data = auto_resp.json()["data"]
    assert auto_data["item_code"] == "host_password_policy_check"

    manual_resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={
            "evidence_id": evidence_id,
            "selected_item_code": "identity_password_policy_check",
            "force_regenerate": True,
        },
    )
    assert manual_resp.status_code == 201
    manual_data = manual_resp.json()["data"]
    assert manual_data["item_code"] == "identity_password_policy_check"
    assert manual_data["template_code"] == "identity_password_policy"
    assert manual_data["match_reasons"]["selection_mode"] == "manual_item"
    assert manual_data["match_reasons"]["best_match_item_code"] == "host_password_policy_check"
    assert "人工选择候选项生成" in manual_data["review_comment"]


def test_record_update_rejects_direct_export_from_reviewed(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "policy_missing_action.txt")
    run_extract_flow(client, evidence_id, "security_policy_missing_action", "security_policy_basic")

    resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={"evidence_id": evidence_id},
    )
    assert resp.status_code == 201
    record = resp.json()["data"]
    assert record["status"] == "reviewed"

    update_resp = client.put(
        f"/api/v1/records/{record['id']}",
        json={
            "status": "exported",
            "review_comment": "非法跳过审批",
            "reviewed_by": "carol",
        },
    )
    assert update_resp.status_code == 400
    assert update_resp.json()["error"]["code"] == "INVALID_RECORD_STATUS_TRANSITION"


def test_records_storage_path_is_under_project_backend_dir():
    assert Path(settings.BASE_DIR).name == "backend"
