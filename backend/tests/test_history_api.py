from openpyxl import Workbook

from app.models.assessment_template import TemplateHistoryLink
from tests.assessment_template_excel_utils import build_assessment_template_excel
from tests.history_excel_utils import (
    build_final_assessment_excel,
    build_history_excel,
    build_history_excel_with_cover_sheet,
    build_history_excel_with_trailing_blank_headers,
    build_history_excel_with_variation_headers,
)
from tests.test_guidance_api import configure_guidance_path, write_guidance_file


PHRASE_QUERY = {
    "control_point": "边界访问控制",
    "evaluation_item": "应限制非授权访问",
    "asset_type": "firewall",
}


def import_sample_history(client):
    resp = client.post(
        "/api/v1/history/import-excel",
        files={"file": ("history.xlsx", build_history_excel(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 201
    return resp.json()["data"]


def import_assessment_template(client):
    resp = client.post(
        "/api/v1/assessment-templates/import-excel",
        files={"file": ("template.xlsx", build_assessment_template_excel(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 201
    return resp.json()["data"]


def import_network_guidance(client, tmp_path):
    content = """
# 网络安全
## 边界防护
应核查出口防火墙访问控制策略。
应查看访问控制日志留存情况。
记录建议：经现场核查，防火墙已配置访问控制策略，并开启日志留存。
""".strip()
    file_path = write_guidance_file(tmp_path, content)
    configure_guidance_path(file_path)
    resp = client.post("/api/v1/guidance/import-md")
    assert resp.status_code == 201
    return client.get("/api/v1/guidance/items").json()["data"]["items"][0]["id"]


def build_missing_header_excel() -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "错误表"
    worksheet.append(["错误列", "控制点", "测评项", "结果记录", "符合情况", "分值", "编号"])
    worksheet.append(["安全通信网络", "边界访问控制", "应限制非授权访问", "已配置", "符合", 1.0, "A-01"])

    from io import BytesIO

    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def test_import_history_excel_api(client):
    data = import_sample_history(client)

    assert data["sheet_count"] == 2
    assert data["imported_count"] == 4
    assert data["compliance_status_counts"]["符合"] == 1


def test_update_and_delete_history_record(client):
    import_sample_history(client)
    record = client.get("/api/v1/history-records").json()["data"]["items"][0]

    update_resp = client.patch(
        f"/api/v1/history-records/{record['id']}",
        json={"control_point": "新的控制点", "record_text": "新的记录内容"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["data"]
    assert updated["control_point"] == "新的控制点"
    assert updated["record_text"] == "新的记录内容"

    delete_resp = client.delete(f"/api/v1/history-records/{record['id']}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"]["id"] == record["id"]


def test_delete_history_record_requires_force_when_linked(client, db_session):
    import_sample_history(client)
    import_assessment_template(client)
    record = client.get("/api/v1/history-records").json()["data"]["items"][0]
    template_item = client.get("/api/v1/assessment-templates/items").json()["data"]["items"][0]

    db_session.add(
        TemplateHistoryLink(
            template_item_id=template_item["id"],
            history_record_id=record["id"],
            match_score=0.9,
            match_reason={"reason": "test"},
        )
    )
    db_session.commit()

    resp = client.delete(f"/api/v1/history-records/{record['id']}")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "HISTORY_RECORD_IN_USE"

    force_resp = client.delete(f"/api/v1/history-records/{record['id']}", params={"force": True})
    assert force_resp.status_code == 200
    data = force_resp.json()["data"]
    assert data["linked_template_count"] == 1
    assert data["forced"] is True


def test_delete_history_records_by_source(client):
    import_sample_history(client)
    data = client.get("/api/v1/history-records").json()["data"]["items"]
    source_file = data[0]["source_file"]

    delete_resp = client.delete("/api/v1/history-records/by-source", params={"source_file": source_file})
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"]["deleted_count"] >= 1


def test_import_final_assessment_excel_api_parses_asset_metadata_and_inherited_columns(client):
    resp = client.post(
        "/api/history-records/import-excel",
        files={"file": ("final.xlsx", build_final_assessment_excel(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["imported_count"] == 2

    list_resp = client.get("/api/history-records", params={"asset_name": "出口防火墙-A"})
    assert list_resp.status_code == 200
    rows = list_resp.json()["data"]["items"]
    assert len(rows) == 2
    first = rows[0] if rows[0]["item_code"] == "A-01" else rows[1]
    second = rows[0] if rows[0]["item_code"] == "A-02" else rows[1]
    assert first["asset_name"] == "出口防火墙-A"
    assert first["asset_ip"] == "143.8.51.2"
    assert first["asset_version"] == "V8.0.26"
    assert second["standard_type"] == "安全通信网络"
    assert second["control_point"] == "边界访问控制"
    assert second["raw_text"] == "查看日志审计配置，当前已开启日志留存。"
    assert second["record_text"] == "查看日志审计配置，当前已开启日志留存。"
    assert second["compliance_result"] == "部分符合"
    assert second["score_weight"] == 0.6


def test_history_records_search_similar_api(client):
    client.post(
        "/api/history-records/import-excel",
        files={"file": ("final.xlsx", build_final_assessment_excel(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    resp = client.post(
        "/api/history-records/search-similar",
        json={
            "ocr_text": "访问控制策略 日志审计",
            "asset_type": "firewall",
            "page_type": "出口防火墙",
            "control_point": "边界访问控制",
            "item_text": "应限制非授权访问",
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data
    assert data[0]["asset_name"] == "出口防火墙-A"
    assert data[0]["score"] >= data[-1]["score"]


def test_import_history_excel_api_accepts_variation_headers(client):
    resp = client.post(
        "/api/v1/history/import-excel",
        files={"file": ("history.xlsx", build_history_excel_with_variation_headers(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["imported_count"] == 1


def test_import_history_excel_api_accepts_trailing_blank_headers(client):
    resp = client.post(
        "/api/v1/history/import-excel",
        files={"file": ("history.xlsx", build_history_excel_with_trailing_blank_headers(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["imported_count"] == 1


def test_import_history_excel_api_skips_cover_sheet(client):
    resp = client.post(
        "/api/v1/history/import-excel",
        files={"file": ("history.xlsx", build_history_excel_with_cover_sheet(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["sheet_count"] == 2
    assert data["imported_count"] == 1


def test_list_history_records_and_detail(client):
    import_sample_history(client)

    list_resp = client.get("/api/v1/history/records", params={"asset_type": "firewall"})
    assert list_resp.status_code == 200
    rows = list_resp.json()["data"]["items"]
    assert len(rows) == 2
    assert all(row["asset_type"] == "firewall" for row in rows)

    detail_resp = client.get(f"/api/v1/history/records/{rows[0]['id']}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["data"]["sheet_name"] == "出口防火墙"


def test_search_history_records(client):
    import_sample_history(client)

    resp = client.get("/api/v1/history/search", params={"keyword": "日志审计"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["item_no"] == "A-02"


def test_history_stats_api(client):
    import_sample_history(client)

    resp = client.get("/api/v1/history/stats")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["sheet_count"] == 2
    assert data["total"] == 4
    assert data["asset_type_counts"]["firewall"] == 2
    assert data["asset_type_counts"]["switch"] == 2


def test_history_similar_api(client):
    import_sample_history(client)

    resp = client.get("/api/v1/history/similar", params=PHRASE_QUERY)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    assert data[0]["asset_type"] == "firewall"
    assert data[0]["score"] >= data[-1]["score"]


def test_history_phrases_api(client):
    import_sample_history(client)

    resp = client.get("/api/v1/history/phrases")
    assert resp.status_code == 200
    data = resp.json()["data"]
    phrase_map = {item["phrase"]: item for item in data}
    assert phrase_map["经现场核查"]["total"] == 1
    assert phrase_map["查看"]["compliance_status_counts"]["部分符合"] == 1
    assert phrase_map["不适用"]["compliance_status_counts"]["不适用"] == 1


def test_import_history_excel_rejects_invalid_file(client):
    resp = client.post(
        "/api/v1/history/import-excel",
        files={"file": ("history.txt", b"invalid", "text/plain")},
    )

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "HISTORY_EXCEL_INVALID_TYPE"


def test_import_history_excel_rejects_missing_header(client):
    resp = client.post(
        "/api/v1/history/import-excel",
        files={"file": ("history.xlsx", build_missing_header_excel(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "HISTORY_EXCEL_HEADER_NOT_FOUND"


def test_history_guidance_items_api_returns_reverse_links(client, tmp_path):
    guidance_id = import_network_guidance(client, tmp_path)
    import_sample_history(client)
    client.post(f"/api/v1/guidance/{guidance_id}/link-history")

    history_rows = client.get(f"/api/v1/guidance/{guidance_id}/history-records").json()["data"]["items"]
    history_id = history_rows[0]["history_record_id"]

    resp = client.get(f"/api/v1/history/{history_id}/guidance-items")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data
    assert data[0]["guidance_item_id"] == guidance_id
    assert "section_title" in data[0]
    assert "guidance_code" in data[0]


def test_history_guidance_items_api_rejects_missing_history(client):
    resp = client.get("/api/v1/history/not-exists/guidance-items")

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "HISTORY_RECORD_NOT_FOUND"
