from pathlib import Path

from app.core.config import settings


def create_project(client):
    resp = client.post(
        "/api/v1/projects",
        json={"code": "PJT-EVD", "name": "证据项目", "project_type": "等级保护测评", "status": "draft"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def upload_evidence(client, project_id: str, filename: str = "firewall_basic.txt") -> str:
    upload_resp = client.post(
        f"/api/v1/projects/{project_id}/evidences/upload",
        files={"file": (filename, b"hello evidence", "text/plain")},
        data={
            "title": "配置截图",
            "evidence_type": "screenshot",
            "summary": "边界防护",
            "device": "FW-01",
            "tags_json": '["tag-a", "tag-b"]',
            "source_ref": "manual-upload",
        },
    )
    assert upload_resp.status_code == 201
    upload_body = upload_resp.json()
    assert upload_body["success"] is True
    return upload_body["data"]["id"]


def test_evidence_upload_and_delete(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id)

    upload_dir = Path(settings.UPLOAD_DIR) / project_id
    assert upload_dir.exists()
    assert any(upload_dir.iterdir())

    list_resp = client.get(f"/api/v1/projects/{project_id}/evidences")
    assert list_resp.status_code == 200
    list_body = list_resp.json()
    assert list_body["meta"]["total"] == 1
    assert list_body["data"][0]["title"] == "配置截图"

    get_resp = client.get(f"/api/v1/evidences/{evidence_id}")
    assert get_resp.status_code == 200
    evidence = get_resp.json()["data"]
    assert evidence["device"] == "FW-01"
    assert evidence["asset_id"] is not None

    delete_resp = client.delete(f"/api/v1/evidences/{evidence_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["message"] == "证据已删除"

    missing_resp = client.get(f"/api/v1/evidences/{evidence_id}")
    assert missing_resp.status_code == 404
    assert missing_resp.json()["error"]["code"] == "EVIDENCE_NOT_FOUND"


def test_upload_evidence_under_missing_project(client):
    resp = client.post(
        "/api/v1/projects/missing-project/evidences/upload",
        files={"file": ("evidence.txt", b"hello evidence", "text/plain")},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_run_ocr_and_extract_fields(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")

    ocr_resp = client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "firewall_basic"})
    assert ocr_resp.status_code == 200
    ocr_body = ocr_resp.json()
    assert ocr_body["message"] == "OCR执行成功"
    assert ocr_body["data"]["ocr_status"] == "completed"
    assert ocr_body["data"]["ocr_provider"] == "mock_ocr"
    assert "设备名称" in ocr_body["data"]["text_content"]

    ocr_result_resp = client.get(f"/api/v1/evidences/{evidence_id}/ocr-result")
    assert ocr_result_resp.status_code == 200
    ocr_result = ocr_result_resp.json()["data"]
    assert ocr_result["sample_id"] == "firewall_basic"
    assert ocr_result["status"] == "completed"

    extract_resp = client.post(
        f"/api/v1/evidences/{evidence_id}/extract-fields",
        json={"template_code": "security_device_basic"},
    )
    assert extract_resp.status_code == 200
    extract_body = extract_resp.json()
    assert extract_body["message"] == "字段抽取完成"
    assert extract_body["meta"]["total"] == 4

    fields = {item["field_name"]: item for item in extract_body["data"]}
    assert fields["device_name"]["raw_value"] == "FW-O1"
    assert fields["device_name"]["corrected_value"] == "FW-01"
    assert fields["device_name"]["status"] == "corrected"
    assert fields["device_ip"]["corrected_value"] == "10.0.0.1"

    list_fields_resp = client.get(f"/api/v1/evidences/{evidence_id}/fields")
    assert list_fields_resp.status_code == 200
    list_fields_body = list_fields_resp.json()
    assert list_fields_body["meta"]["total"] == 4


def test_extract_fields_without_ocr_returns_400(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id)

    resp = client.post(f"/api/v1/evidences/{evidence_id}/extract-fields", json={})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "OCR_TEXT_NOT_FOUND"


def test_run_ocr_with_invalid_sample_returns_400(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id)

    resp = client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "missing-sample"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "MOCK_OCR_SAMPLE_NOT_FOUND"
