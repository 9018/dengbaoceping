

def create_project(client):
    resp = client.post(
        "/api/v1/projects",
        json={"code": "PJT-EXP", "name": "导出项目", "project_type": "等级保护测评", "status": "draft"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def upload_evidence(client, project_id: str, filename: str, title: str, device: str) -> str:
    upload_resp = client.post(
        f"/api/v1/projects/{project_id}/evidences/upload",
        files={"file": (filename, f"hello export {filename}".encode("utf-8"), "text/plain")},
        data={
            "title": title,
            "evidence_type": "screenshot",
            "summary": "导出测试",
            "device": device,
            "tags_json": '["export"]',
            "source_ref": "test-export",
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


def generate_record(client, project_id: str, evidence_id: str):
    resp = client.post(
        f"/api/v1/projects/{project_id}/records/generate",
        json={"evidence_id": evidence_id},
    )
    assert resp.status_code == 201
    return resp.json()["data"]


def advance_record_to_approved(client, record_id: str, current_status: str, reviewer: str):
    if current_status == "generated":
        review_resp = client.post(
            f"/api/v1/records/{record_id}/review",
            json={
                "status": "reviewed",
                "final_content": f"{record_id}-reviewed",
                "review_comment": "进入复核",
                "reviewed_by": reviewer,
            },
        )
        assert review_resp.status_code == 200
        current_status = "reviewed"

    if current_status == "reviewed":
        approve_resp = client.post(
            f"/api/v1/records/{record_id}/review",
            json={
                "status": "approved",
                "final_content": f"{record_id}-approved",
                "review_comment": "审批通过",
                "reviewed_by": reviewer,
            },
        )
        assert approve_resp.status_code == 200
        current_status = "approved"

    return current_status



def test_project_export_txt_grouped_by_device(client):
    project_id = create_project(client)
    evidence_id_1 = upload_evidence(client, project_id, "firewall_basic.txt", "防火墙配置", "服务器A")
    evidence_id_2 = upload_evidence(client, project_id, "policy_missing_action.txt", "安全策略", "服务器A")
    evidence_id_3 = upload_evidence(client, project_id, "windows_host_partial.txt", "主机检查", "交换机B")

    run_extract_flow(client, evidence_id_1, "firewall_basic", "security_device_basic")
    run_extract_flow(client, evidence_id_2, "security_policy_missing_action", "security_policy_basic")
    run_extract_flow(client, evidence_id_3, "windows_host_partial", "host_basic_info")

    record_1 = generate_record(client, project_id, evidence_id_1)
    record_2 = generate_record(client, project_id, evidence_id_2)
    record_3 = generate_record(client, project_id, evidence_id_3)

    assert advance_record_to_approved(client, record_1["id"], record_1["status"], "alice") == "approved"
    assert advance_record_to_approved(client, record_2["id"], record_2["status"], "bob") == "approved"
    assert advance_record_to_approved(client, record_3["id"], record_3["status"], "carol") == "approved"

    export_resp = client.post(f"/api/v1/projects/{project_id}/export", json={"format": "txt"})
    assert export_resp.status_code == 201
    export_body = export_resp.json()
    assert export_body["message"] == "项目导出成功"
    export_id = export_body["data"]["id"]
    assert export_body["data"]["record_count"] == 3
    assert export_body["data"]["format"] == "txt"

    jobs_resp = client.get(f"/api/v1/projects/{project_id}/export-jobs")
    assert jobs_resp.status_code == 200
    jobs_body = jobs_resp.json()
    assert jobs_body["meta"]["total"] == 1
    assert jobs_body["data"][0]["id"] == export_id

    download_resp = client.get(f"/api/v1/exports/{export_id}/download")
    assert download_resp.status_code == 200
    content = download_resp.text
    assert "项目：导出项目" in content
    assert "设备：服务器A" in content
    assert "设备：交换机B" in content
    assert record_1["title"] in content
    assert record_2["title"] in content
    assert record_3["title"] in content
    assert "状态：exported" in content


def test_project_export_requires_approved_records(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt", "防火墙配置", "服务器A")
    run_extract_flow(client, evidence_id, "firewall_basic", "security_device_basic")
    record = generate_record(client, project_id, evidence_id)
    assert record["status"] == "generated"

    export_resp = client.post(f"/api/v1/projects/{project_id}/export", json={"format": "txt"})
    assert export_resp.status_code == 400
    assert export_resp.json()["error"]["code"] == "RECORD_NOT_READY_FOR_EXPORT"


def test_project_export_unsupported_format(client):
    project_id = create_project(client)

    export_resp = client.post(f"/api/v1/projects/{project_id}/export", json={"format": "pdf"})
    assert export_resp.status_code == 400
    assert export_resp.json()["error"]["code"] == "EXPORT_FORMAT_NOT_SUPPORTED"
