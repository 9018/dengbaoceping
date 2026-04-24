def test_project_crud(client):
    create_resp = client.post(
        "/api/v1/projects",
        json={
            "code": "PJT-001",
            "name": "等保项目A",
            "project_type": "等级保护测评",
            "status": "draft",
            "description": "项目说明",
        },
    )
    assert create_resp.status_code == 201
    create_body = create_resp.json()
    assert create_body["success"] is True
    project_id = create_body["data"]["id"]

    duplicate_resp = client.post(
        "/api/v1/projects",
        json={
            "code": "PJT-001",
            "name": "重复项目",
            "project_type": "等级保护测评",
            "status": "draft",
        },
    )
    assert duplicate_resp.status_code == 400
    assert duplicate_resp.json()["error"]["code"] == "PROJECT_CODE_EXISTS"

    list_resp = client.get("/api/v1/projects")
    assert list_resp.status_code == 200
    list_body = list_resp.json()
    assert list_body["meta"]["total"] == 1

    get_resp = client.get(f"/api/v1/projects/{project_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["name"] == "等保项目A"

    update_resp = client.put(
        f"/api/v1/projects/{project_id}",
        json={"status": "active", "description": "已启动"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["status"] == "active"

    delete_resp = client.delete(f"/api/v1/projects/{project_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["message"] == "项目已删除"

    missing_resp = client.get(f"/api/v1/projects/{project_id}")
    assert missing_resp.status_code == 404
    assert missing_resp.json()["error"]["code"] == "PROJECT_NOT_FOUND"
