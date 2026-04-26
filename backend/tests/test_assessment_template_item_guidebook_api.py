from pathlib import Path

from tests.assessment_template_excel_utils import build_assessment_template_match_excel
from tests.test_guidance_api import configure_guidance_path, write_guidance_file


GUIDANCE_CONTENT = """
# 网络安全
## 身份鉴别
应核查管理员身份鉴别机制。
应查看密码安全策略、口令复杂度、最小密码长度和登录失败锁定阈值配置。
应提供密码策略截图或 display password-control、display password policy 命令输出。
记录建议：经现场核查，管理员账号已启用口令复杂度、最小密码长度和登录失败锁定策略。

## 安全审计
应核查管理员操作日志留存情况。
应查看审计日志、操作日志和管理员操作记录。
应提供日志页面截图或日志审计配置截图。
预期结果：应提供管理员操作日志留存记录。
""".strip()


def import_assessment_template_match_library(client):
    resp = client.post(
        "/api/v1/assessment-templates/import-excel",
        files={
            "file": (
                "结果记录参考模板20260426.xlsx",
                build_assessment_template_match_excel(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]


def import_template_guidance(client, tmp_path: Path):
    guidance_path = write_guidance_file(tmp_path, GUIDANCE_CONTENT)
    configure_guidance_path(guidance_path)
    resp = client.post("/api/v1/guidance/import-md")
    assert resp.status_code == 201
    return resp.json()["data"]


def test_template_item_link_guidebook_and_list_api(client, tmp_path: Path):
    import_template_guidance(client, tmp_path)
    import_assessment_template_match_library(client)

    items_resp = client.get(
        "/api/v1/assessment-templates/items",
        params={"sheet_name": "外联防火墙A", "item_code": "A-01"},
    )
    assert items_resp.status_code == 200
    item_id = items_resp.json()["data"][0]["id"]

    link_resp = client.post(f"/api/v1/assessment-template-items/{item_id}/link-guidebook")
    assert link_resp.status_code == 200
    assert link_resp.json()["data"]["linked_count"] >= 1

    list_resp = client.get(f"/api/v1/assessment-template-items/{item_id}/guidebook-links")
    assert list_resp.status_code == 200
    rows = list_resp.json()["data"]
    assert rows
    assert rows[0]["template_item_id"] == item_id
    assert "guidance_item" in rows[0]
    assert "section_title" in rows[0]
    assert "check_points" in rows[0]
    assert "evidence_requirements" in rows[0]


def test_template_item_link_guidebook_acceptance_case_hits_identity_guidance(client, tmp_path: Path):
    import_template_guidance(client, tmp_path)
    import_assessment_template_match_library(client)

    items_resp = client.get(
        "/api/v1/assessment-templates/items",
        params={"sheet_name": "外联防火墙A", "item_code": "A-01"},
    )
    item_id = items_resp.json()["data"][0]["id"]

    client.post(f"/api/v1/assessment-template-items/{item_id}/link-guidebook")
    rows = client.get(f"/api/v1/assessment-template-items/{item_id}/guidebook-links").json()["data"]

    assert rows[0]["section_title"] == "身份鉴别"
    assert rows[0]["match_score"] >= 0.4
    assert any("控制点" in reason or "测评项" in reason or "证据要求" in reason for reason in rows[0]["match_reason"]["summary"])


def test_template_item_link_guidebook_api_rejects_missing_item(client):
    resp = client.post("/api/v1/assessment-template-items/not-exists/link-guidebook")

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ASSESSMENT_TEMPLATE_ITEM_NOT_FOUND"
