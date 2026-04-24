def create_project(client):
    resp = client.post(
        "/api/v1/projects",
        json={"code": "PJT-REV", "name": "复核项目", "project_type": "等级保护测评", "status": "draft"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def upload_evidence(client, project_id: str, filename: str) -> str:
    upload_resp = client.post(
        f"/api/v1/projects/{project_id}/evidences/upload",
        files={"file": (filename, b"hello evidence", "text/plain")},
        data={
            "title": "复核截图",
            "evidence_type": "screenshot",
            "summary": "人工复核",
            "device": "AUTO",
            "tags_json": '["review"]',
            "source_ref": "review-test-upload",
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
    return extract_resp.json()["data"]


def generate_record(client, project_id: str, evidence_id: str):
    resp = client.post(f"/api/v1/projects/{project_id}/records/generate", json={"evidence_id": evidence_id})
    assert resp.status_code == 201
    return resp.json()["data"]


def test_update_and_review_field(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")
    fields = run_extract_flow(client, evidence_id, "firewall_basic", "security_device_basic")
    device_name_field = next(item for item in fields if item["field_name"] == "device_name")

    update_resp = client.put(
        f"/api/v1/fields/{device_name_field['id']}",
        json={
            "corrected_value": "FW-01-MANUAL",
            "status": "corrected",
            "review_comment": "人工修正设备名称",
            "reviewed_by": "alice",
        },
    )
    assert update_resp.status_code == 200
    update_data = update_resp.json()["data"]
    assert update_data["corrected_value"] == "FW-01-MANUAL"
    assert update_data["status"] == "corrected"
    assert update_data["reviewed_by"] == "alice"
    assert update_data["reviewed_at"] is not None

    review_resp = client.post(
        f"/api/v1/fields/{device_name_field['id']}/review",
        json={
            "status": "reviewed",
            "review_comment": "复核通过",
            "reviewed_by": "bob",
        },
    )
    assert review_resp.status_code == 200
    review_data = review_resp.json()["data"]
    assert review_data["status"] == "reviewed"
    assert review_data["review_comment"] == "复核通过"
    assert review_data["reviewed_by"] == "bob"

    logs_resp = client.get(f"/api/v1/fields/{device_name_field['id']}/audit-logs")
    assert logs_resp.status_code == 200
    logs_body = logs_resp.json()
    assert logs_body["meta"]["total"] == 2
    assert logs_body["data"][0]["action"] == "field_review"
    assert logs_body["data"][0]["target_type"] == "field"
    assert logs_body["data"][0]["target_id"] == device_name_field["id"]
    assert logs_body["data"][0]["reviewed_by"] == "bob"
    assert logs_body["data"][1]["action"] == "field_update"
    assert logs_body["data"][1]["reviewed_by"] == "alice"


def test_field_transition_rejects_return_to_extracted(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")
    fields = run_extract_flow(client, evidence_id, "firewall_basic", "security_device_basic")
    device_name_field = next(item for item in fields if item["field_name"] == "device_name")

    corrected_resp = client.put(
        f"/api/v1/fields/{device_name_field['id']}",
        json={
            "corrected_value": "FW-01-MANUAL",
            "status": "corrected",
            "review_comment": "人工修正设备名称",
            "reviewed_by": "alice",
        },
    )
    assert corrected_resp.status_code == 200

    invalid_resp = client.put(
        f"/api/v1/fields/{device_name_field['id']}",
        json={
            "status": "extracted",
            "review_comment": "错误回退",
            "reviewed_by": "alice",
        },
    )
    assert invalid_resp.status_code == 400
    assert invalid_resp.json()["error"]["code"] == "INVALID_FIELD_STATUS_TRANSITION"



def test_field_transition_allows_missing_to_corrected(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "policy_missing_action.txt")
    fields = run_extract_flow(client, evidence_id, "security_policy_missing_action", "security_policy_basic")
    action_field = next(item for item in fields if item["field_name"] == "action")
    assert action_field["status"] == "missing"

    update_resp = client.put(
        f"/api/v1/fields/{action_field['id']}",
        json={
            "corrected_value": "allow",
            "status": "corrected",
            "review_comment": "补录缺失动作",
            "reviewed_by": "alice",
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["status"] == "corrected"
    assert update_resp.json()["data"]["corrected_value"] == "allow"


def test_generate_record_prefers_corrected_value_and_supports_record_review(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")
    fields = run_extract_flow(client, evidence_id, "firewall_basic", "security_device_basic")
    device_name_field = next(item for item in fields if item["field_name"] == "device_name")

    field_fix_resp = client.put(
        f"/api/v1/fields/{device_name_field['id']}",
        json={
            "corrected_value": "FW-REVIEWED-01",
            "status": "corrected",
            "review_comment": "复核后采用人工值",
            "reviewed_by": "alice",
        },
    )
    assert field_fix_resp.status_code == 200

    record = generate_record(client, project_id, evidence_id)
    assert "FW-REVIEWED-01" in record["record_content"]
    assert record["final_content"] == record["record_content"]

    update_resp = client.put(
        f"/api/v1/records/{record['id']}",
        json={
            "record_content": "人工调整后的正文",
            "final_content": "人工调整后的最终正文",
            "status": "reviewed",
            "review_comment": "更新记录正文",
            "reviewed_by": "carol",
        },
    )
    assert update_resp.status_code == 200
    update_data = update_resp.json()["data"]
    assert update_data["record_content"] == "人工调整后的正文"
    assert update_data["final_content"] == "人工调整后的最终正文"
    assert update_data["status"] == "reviewed"
    assert update_data["reviewed_by"] == "carol"

    review_resp = client.post(
        f"/api/v1/records/{record['id']}/review",
        json={
            "status": "approved",
            "final_content": "最终确认版本",
            "review_comment": "审批通过",
            "reviewed_by": "dave",
        },
    )
    assert review_resp.status_code == 200
    review_data = review_resp.json()["data"]
    assert review_data["status"] == "approved"
    assert review_data["final_content"] == "最终确认版本"
    assert review_data["review_comment"] == "审批通过"
    assert review_data["reviewed_by"] == "dave"
    assert review_data["reviewed_at"] is not None

    logs_resp = client.get(f"/api/v1/records/{record['id']}/audit-logs")
    assert logs_resp.status_code == 200
    logs_body = logs_resp.json()
    assert logs_body["meta"]["total"] == 2
    assert logs_body["data"][0]["action"] == "record_review"
    assert logs_body["data"][0]["target_type"] == "record"
    assert logs_body["data"][0]["target_id"] == record["id"]
    assert logs_body["data"][0]["reviewed_by"] == "dave"
    assert logs_body["data"][1]["action"] == "record_update"
    assert logs_body["data"][1]["reviewed_by"] == "carol"



def test_record_transition_rejects_approve_from_generated(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")
    run_extract_flow(client, evidence_id, "firewall_basic", "security_device_basic")
    record = generate_record(client, project_id, evidence_id)
    assert record["status"] == "generated"

    invalid_resp = client.post(
        f"/api/v1/records/{record['id']}/review",
        json={
            "status": "approved",
            "final_content": "跳过 review",
            "review_comment": "非法跳转",
            "reviewed_by": "dave",
        },
    )
    assert invalid_resp.status_code == 400
    assert invalid_resp.json()["error"]["code"] == "INVALID_RECORD_STATUS_TRANSITION"
