from pathlib import Path

import pytest

from app.core.config import settings
from app.models.assessment_template import TemplateGuidebookLink
from app.models.evidence import Evidence
from app.models.project import Project
from tests.assessment_template_excel_utils import build_assessment_template_excel
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


def import_duplicate_guidance(client, tmp_path: Path):
    content = """
# 网络安全
## 边界防护-A
应核查出口防火墙访问控制策略。
应查看访问控制日志留存情况。
记录建议：经现场核查，防火墙已配置访问控制策略，并开启日志留存。
## 边界防护-B
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


def import_assessment_template(client):
    return client.post(
        "/api/v1/assessment-templates/import-excel",
        files={"file": ("template.xlsx", build_assessment_template_excel(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
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
    assert items_data["total"] == 3
    assert len(items_data["items"]) == 3

    detail_item = next(item for item in items_data["items"] if item["section_title"] == "安全通用要求")
    detail_resp = client.get(f"/api/v1/guidance/items/{detail_item['id']}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["data"]["section_title"] == "安全通用要求"


def test_guidance_summary_api(client, tmp_path: Path):
    import_sample_guidance(client, tmp_path)
    import_duplicate_guidance(client, tmp_path)

    resp = client.get("/api/v1/guidance/summary")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 3
    assert data["source_file_count"] == 1
    assert data["duplicate_group_count"] == 1
    assert data["duplicate_item_count"] == 2
    assert data["level1_counts"]["网络安全"] == 3
    assert data["level2_counts"]["边界防护-A"] == 1


def test_guidance_duplicates_api_and_keep_first(client, tmp_path: Path):
    import_duplicate_guidance(client, tmp_path)

    list_resp = client.get("/api/v1/guidance/duplicates")
    assert list_resp.status_code == 200
    groups = list_resp.json()["data"]
    assert len(groups) == 1
    assert groups[0]["duplicate_count"] == 2
    assert len(groups[0]["items"]) == 2

    delete_resp = client.delete("/api/v1/guidance/duplicates", params={"strategy": "keep_first"})
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"]["deleted_count"] == 1

    after_resp = client.get("/api/v1/guidance/duplicates")
    assert after_resp.status_code == 200
    assert after_resp.json()["data"] == []


def test_guidance_duplicates_force_required_when_linked(client, db_session, tmp_path: Path):
    import_assessment_template(client)
    import_duplicate_guidance(client, tmp_path)
    groups = client.get("/api/v1/guidance/duplicates").json()["data"]
    duplicate_item = groups[0]["items"][1]
    template_item = client.get("/api/v1/assessment-templates/items").json()["data"]["items"][0]

    db_session.add(
        TemplateGuidebookLink(
            template_item_id=template_item["id"],
            guidance_item_id=duplicate_item["id"],
            match_score=0.88,
            match_reason={"reason": "duplicate-link"},
        )
    )
    db_session.commit()

    resp = client.delete("/api/v1/guidance/duplicates", params={"strategy": "keep_first"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "GUIDANCE_ITEM_IN_USE"

    force_resp = client.delete("/api/v1/guidance/duplicates", params={"strategy": "keep_first", "force": True})
    assert force_resp.status_code == 200
    assert force_resp.json()["data"]["linked_template_count"] == 1
    assert force_resp.json()["data"]["forced"] is True


def test_guidance_duplicates_force_clears_history_and_evidence_links(client, db_session, tmp_path: Path):
    import_duplicate_guidance(client, tmp_path)
    groups = client.get("/api/v1/guidance/duplicates").json()["data"]
    duplicate_item = groups[0]["items"][1]

    project = Project(code="PJT-GUIDE", name="指导书测试项目", project_type="等级保护测评", status="draft")
    db_session.add(project)
    db_session.flush()
    db_session.add(Evidence(project_id=project.id, evidence_type="image", title="evidence", matched_guidance_id=duplicate_item["id"]))
    db_session.commit()

    force_resp = client.delete("/api/v1/guidance/duplicates", params={"strategy": "keep_first", "force": True})
    assert force_resp.status_code == 200
    assert force_resp.json()["data"]["matched_evidence_count"] == 1


def test_update_and_delete_guidance_item(client, tmp_path: Path):
    import_sample_guidance(client, tmp_path)
    item = client.get("/api/v1/guidance/items").json()["data"]["items"][0]

    update_resp = client.patch(
        f"/api/v1/guidance/items/{item['id']}",
        json={"section_title": "新的章节标题", "record_suggestion": "新的记录建议"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["data"]
    assert updated["section_title"] == "新的章节标题"
    assert updated["record_suggestion"] == "新的记录建议"

    delete_resp = client.delete(f"/api/v1/guidance/items/{item['id']}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"]["id"] == item["id"]


def test_delete_guidance_item_requires_force_when_linked(client, db_session, tmp_path: Path):
    import_network_guidance(client, tmp_path)
    import_sample_history(client)
    import_assessment_template(client)
    guidance_id = client.get("/api/v1/guidance/items").json()["data"]["items"][0]["id"]
    template_item_id = client.get("/api/v1/assessment-templates/items").json()["data"]["items"][0]["id"]
    client.post(f"/api/v1/guidance/{guidance_id}/link-history")

    db_session.add(
        TemplateGuidebookLink(
            template_item_id=template_item_id,
            guidance_item_id=guidance_id,
            match_score=0.9,
            match_reason={"reason": "test"},
        )
    )
    db_session.commit()

    resp = client.delete(f"/api/v1/guidance/items/{guidance_id}")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "GUIDANCE_ITEM_IN_USE"

    force_resp = client.delete(f"/api/v1/guidance/items/{guidance_id}", params={"force": True})
    assert force_resp.status_code == 200
    data = force_resp.json()["data"]
    assert data["linked_template_count"] == 1
    assert data["linked_history_count"] >= 1


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
    rows = list_resp.json()["data"]["items"]
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
    data = resp.json()["data"]["items"]
    assert data
    assert all(item["compliance_status"] == "符合" for item in data)


def test_guidance_link_history_api_rejects_missing_guidance(client):
    resp = client.post("/api/v1/guidance/not-exists/link-history")

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "GUIDANCE_ITEM_NOT_FOUND"
