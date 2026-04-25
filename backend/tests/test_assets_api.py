def create_project(client):
    resp = client.post(
        "/api/v1/projects",
        json={"code": "PJT-SET", "name": "资产项目", "project_type": "等级保护测评", "status": "draft"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def test_asset_crud(client):
    project_id = create_project(client)

    create_resp = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "category": "report",
            "category_label": "报告文件",
            "batch_no": "batch-001",
            "filename": "report.pdf",
            "primary_ip": "10.0.0.9",
            "file_ext": ".pdf",
            "mime_type": "application/pdf",
            "relative_path": "uploads/report.pdf",
            "absolute_path": "/tmp/report.pdf",
            "file_size": 123,
            "file_sha256": "abc123",
            "source": "manual",
            "ingest_status": "pending",
        },
    )
    assert create_resp.status_code == 201
    create_body = create_resp.json()
    assert create_body["success"] is True
    asset_id = create_body["data"]["id"]
    assert create_body["data"]["asset_kind"] == "test_object"
    assert create_body["data"]["primary_ip"] == "10.0.0.9"

    list_resp = client.get(f"/api/v1/projects/{project_id}/assets")
    assert list_resp.status_code == 200
    assert list_resp.json()["meta"]["total"] == 1

    get_resp = client.get(f"/api/v1/assets/{asset_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["filename"] == "report.pdf"
    assert get_resp.json()["data"]["primary_ip"] == "10.0.0.9"

    update_resp = client.put(
        f"/api/v1/assets/{asset_id}",
        json={"ingest_status": "processed", "category_label": "正式报告", "primary_ip": "10.0.0.10"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["ingest_status"] == "processed"
    assert update_resp.json()["data"]["primary_ip"] == "10.0.0.10"

    delete_resp = client.delete(f"/api/v1/assets/{asset_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["message"] == "文件资产已删除"

    missing_resp = client.get(f"/api/v1/assets/{asset_id}")
    assert missing_resp.status_code == 404
    assert missing_resp.json()["error"]["code"] == "ASSET_NOT_FOUND"


def test_create_asset_under_missing_project(client):
    resp = client.post(
        "/api/v1/projects/missing-project/assets",
        json={
            "category": "report",
            "category_label": "报告文件",
            "filename": "report.pdf",
            "relative_path": "uploads/report.pdf",
        },
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PROJECT_NOT_FOUND"
