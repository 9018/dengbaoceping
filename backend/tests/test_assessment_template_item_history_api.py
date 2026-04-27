from io import BytesIO

from openpyxl import Workbook

from tests.assessment_template_excel_utils import build_assessment_template_match_excel
from tests.test_history_api import import_sample_history


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


def build_identity_history_excel() -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "出口防火墙"
    worksheet.append(["扩展标准", "控制点", "测评项", "结果记录", "符合情况", "分值", "编号"])
    worksheet.append([
        "安全通信网络",
        "身份鉴别",
        "应对管理员身份进行鉴别",
        "经现场核查，管理员账号已启用口令认证，并配置最小密码长度、密码复杂度和有效期。",
        "符合",
        1.0,
        "A-01",
    ])
    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def import_identity_history(client):
    resp = client.post(
        "/api/v1/history/import-excel",
        files={"file": ("identity-history.xlsx", build_identity_history_excel(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 201
    return resp.json()["data"]


def test_template_item_link_history_and_list_api(client):
    import_sample_history(client)
    import_assessment_template_match_library(client)

    items_resp = client.get(
        "/api/v1/assessment-templates/items",
        params={"sheet_name": "外联防火墙A", "item_code": "A-01"},
    )
    assert items_resp.status_code == 200
    item_id = items_resp.json()["data"]["items"][0]["id"]

    link_resp = client.post(f"/api/v1/assessment-template-items/{item_id}/link-history")
    assert link_resp.status_code == 200
    assert link_resp.json()["data"]["linked_count"] >= 1

    list_resp = client.get(f"/api/v1/assessment-template-items/{item_id}/history-links")
    assert list_resp.status_code == 200
    rows = list_resp.json()["data"]
    assert rows
    assert rows[0]["template_item_id"] == item_id
    assert "history_record" in rows[0]
    assert "record_text" in rows[0]
    assert "compliance_result" in rows[0]


def test_template_item_history_links_support_compliance_filter(client):
    import_sample_history(client)
    import_assessment_template_match_library(client)

    items_resp = client.get(
        "/api/v1/assessment-templates/items",
        params={"sheet_name": "外联防火墙A", "item_code": "A-01"},
    )
    item_id = items_resp.json()["data"]["items"][0]["id"]

    client.post(f"/api/v1/assessment-template-items/{item_id}/link-history")
    rows = client.get(
        f"/api/v1/assessment-template-items/{item_id}/history-links",
        params={"compliance_result": "符合"},
    ).json()["data"]

    assert rows
    assert all((row["compliance_result"] or row["compliance_status"]) == "符合" for row in rows)


def test_template_item_link_history_acceptance_case_hits_identity_history(client):
    import_identity_history(client)
    import_assessment_template_match_library(client)

    items_resp = client.get(
        "/api/v1/assessment-templates/items",
        params={"sheet_name": "外联防火墙A", "item_code": "A-01"},
    )
    item_id = items_resp.json()["data"]["items"][0]["id"]

    client.post(f"/api/v1/assessment-template-items/{item_id}/link-history")
    rows = client.get(f"/api/v1/assessment-template-items/{item_id}/history-links").json()["data"]

    assert rows[0]["sheet_name"] == "出口防火墙"
    assert rows[0]["match_score"] >= 0.5
    assert any("控制点" in reason or "测评项" in reason or "写法" in reason for reason in rows[0]["match_reason"]["summary"])


def test_template_item_link_history_api_rejects_missing_item(client):
    resp = client.post("/api/v1/assessment-template-items/not-exists/link-history")

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ASSESSMENT_TEMPLATE_ITEM_NOT_FOUND"
