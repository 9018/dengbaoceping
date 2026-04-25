from pathlib import Path

import pytest

from app.core.config import settings
from tests.history_excel_utils import build_history_excel


@pytest.fixture(autouse=True)
def restore_guidance_path():
    original = settings.GUIDANCE_FILE_PATH
    yield
    settings.GUIDANCE_FILE_PATH = original


def write_guidance_file(tmp_path: Path, content: str) -> Path:
    guidance_dir = tmp_path / "md"
    guidance_dir.mkdir(parents=True, exist_ok=True)
    file_path = guidance_dir / "指导书.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def configure_guidance_path(path: Path):
    settings.GUIDANCE_FILE_PATH = str(path)


def import_sample_guidance(client, tmp_path: Path):
    content = """
# 安全物理环境
## 安全通用要求
| 测评项 | 操作步骤 | 预期结果 |
| --- | --- | --- |
| 物理访问控制 | 应核查门禁配置并查看门禁日志 | 应提供门禁记录和现场截图 |
## 云计算安全扩展要求
应核查云平台位于中国境内，并提供建设方案。
""".strip()
    file_path = write_guidance_file(tmp_path, content)
    configure_guidance_path(file_path)
    return client.post("/api/v1/guidance/import-md")


def import_network_guidance(client, tmp_path: Path):
    content = """
# 网络安全
## 边界防护
应核查出口防火墙访问控制策略。
应查看访问控制日志留存情况。
记录建议：经现场核查，防火墙已配置访问控制策略，并开启日志留存。
""".strip()
    file_path = write_guidance_file(tmp_path, content)
    configure_guidance_path(file_path)
    return client.post("/api/v1/guidance/import-md")


def import_sample_history(client):
    return client.post(
        "/api/v1/history/import-excel",
        files={"file": ("history.xlsx", build_history_excel(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )


def test_guidance_import_file_not_found(client, tmp_path: Path):
    configure_guidance_path(tmp_path / "md" / "指导书.md")

    resp = client.post("/api/v1/guidance/import-md")

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "GUIDANCE_MD_NOT_FOUND"


def test_guidance_import_file_empty(client, tmp_path: Path):
    file_path = write_guidance_file(tmp_path, "   \n")
    configure_guidance_path(file_path)

    resp = client.post("/api/v1/guidance/import-md")

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "GUIDANCE_MD_EMPTY"


def test_guidance_import_and_items_api(client, tmp_path: Path):
    resp = import_sample_guidance(client, tmp_path)

    assert resp.status_code == 201
    body = resp.json()
    assert body["data"]["imported_count"] == 3
    assert body["data"]["source_file"] == "md/指导书.md"

    items_resp = client.get("/api/v1/guidance/items")
    assert items_resp.status_code == 200
    items_data = items_resp.json()["data"]
    assert items_data["imported"] is True
    assert items_data["total"] == 3
    assert len(items_data["items"]) == 3

    detail_item = next(item for item in items_data["items"] if item["section_title"] == "安全通用要求")
    detail_resp = client.get(f"/api/v1/guidance/items/{detail_item['id']}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["data"]["section_title"] == "安全通用要求"


def test_guidance_default_path_prefers_repo_md_file(client):
    expected_path = Path(settings.BASE_DIR) / "md" / "指导书.md"
    original = settings.GUIDANCE_FILE_PATH
    settings.GUIDANCE_FILE_PATH = str(expected_path)
    try:
        resp = client.get("/api/v1/guidance/items")
    finally:
        settings.GUIDANCE_FILE_PATH = original

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["absolute_path"].endswith("/md/指导书.md")


def test_guidance_keyword_search(client, tmp_path: Path):
    import_resp = import_sample_guidance(client, tmp_path)
    assert import_resp.status_code == 201

    search_resp = client.get("/api/v1/guidance/search", params={"keyword": "门禁"})
    assert search_resp.status_code == 200
    data = search_resp.json()["data"]
    assert len(data) == 1
    assert data[0]["section_title"] == "安全通用要求"

    items_search_resp = client.get("/api/v1/guidance/items", params={"keyword": "中国境内"})
    assert items_search_resp.status_code == 200
    assert len(items_search_resp.json()["data"]["items"]) == 1


def test_guidance_items_api_shows_empty_status(client, tmp_path: Path):
    file_path = write_guidance_file(tmp_path, "\n")
    configure_guidance_path(file_path)

    resp = client.get("/api/v1/guidance/items")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["file_empty"] is True
    assert data["file_message"] == "指导书.md 当前为空，请先补充内容"


def test_guidance_link_history_and_list_records_api(client, tmp_path: Path):
    guidance_resp = import_network_guidance(client, tmp_path)
    history_resp = import_sample_history(client)
    assert guidance_resp.status_code == 201
    assert history_resp.status_code == 201

    items_resp = client.get("/api/v1/guidance/items")
    guidance_id = items_resp.json()["data"]["items"][0]["id"]

    link_resp = client.post(f"/api/v1/guidance/{guidance_id}/link-history")
    assert link_resp.status_code == 200
    assert link_resp.json()["data"]["linked_count"] >= 1

    list_resp = client.get(f"/api/v1/guidance/{guidance_id}/history-records")
    assert list_resp.status_code == 200
    rows = list_resp.json()["data"]
    assert rows
    assert "match_score" in rows[0]
    assert "match_reason" in rows[0]
    assert "record_text" in rows[0]
    assert "compliance_status" in rows[0]


def test_guidance_history_records_api_supports_status_filter(client, tmp_path: Path):
    guidance_resp = import_network_guidance(client, tmp_path)
    history_resp = import_sample_history(client)
    assert guidance_resp.status_code == 201
    assert history_resp.status_code == 201

    guidance_id = client.get("/api/v1/guidance/items").json()["data"]["items"][0]["id"]
    client.post(f"/api/v1/guidance/{guidance_id}/link-history")

    resp = client.get(
        f"/api/v1/guidance/{guidance_id}/history-records",
        params={"compliance_status": "符合"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data
    assert all(item["compliance_status"] == "符合" for item in data)


def test_guidance_link_history_api_rejects_missing_guidance(client):
    resp = client.post("/api/v1/guidance/not-exists/link-history")

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "GUIDANCE_ITEM_NOT_FOUND"
