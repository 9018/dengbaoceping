from app.models.asset import Asset
from app.models.project import Project
from app.models.project_assessment_table import ProjectAssessmentTable
from tests.assessment_template_excel_utils import build_assessment_template_excel, build_assessment_template_excel_without_header


def import_assessment_template(client, filename: str = "结果记录参考模板20260403.xlsx") -> dict:
    resp = client.post(
        "/api/v1/assessment-templates/import-excel",
        files={"file": (filename, build_assessment_template_excel(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 201
    return resp.json()["data"]


def test_import_assessment_templates_and_query_items(client):
    data = import_assessment_template(client)
    assert data["source_file"] == "结果记录参考模板20260403.xlsx"
    assert data["sheet_count"] == 3
    assert data["item_count"] == 4
    assert data["imported_count"] == 4
    assert data["skipped_count"] >= 1
    assert data["version"] == "20260403"
    assert data["sheet_names"] == ["外联防火墙A", "核心交换机", "Windows服务器"]

    list_resp = client.get("/api/v1/assessment-templates")
    assert list_resp.status_code == 200
    workbooks = list_resp.json()["data"]["items"]
    assert len(workbooks) == 1
    workbook_id = workbooks[0]["id"]
    assert workbooks[0]["item_count"] == 4

    detail_resp = client.get(f"/api/v1/assessment-templates/{workbook_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["sheet_count"] == 3
    assert detail["item_count"] == 4
    assert detail["object_type_counts"]["安全设备"] == 1
    assert detail["object_type_counts"]["网络设备"] == 1
    assert detail["object_type_counts"]["服务器"] == 1
    assert detail["object_category_counts"]["防火墙"] == 1
    assert detail["control_point_counts"]["访问控制"] == 2

    sheets_resp = client.get(f"/api/v1/assessment-templates/{workbook_id}/sheets")
    assert sheets_resp.status_code == 200
    sheets = sheets_resp.json()["data"]["items"]
    assert len(sheets) == 3
    firewall_sheet = next(item for item in sheets if item["sheet_name"] == "外联防火墙A")
    assert firewall_sheet["object_type"] == "安全设备"
    assert firewall_sheet["object_category"] == "防火墙"
    assert firewall_sheet["is_security_device"] is True
    assert firewall_sheet["is_network"] is True
    assert firewall_sheet["row_count"] == 2
    windows_sheet = next(item for item in sheets if item["sheet_name"] == "Windows服务器")
    assert windows_sheet["object_type"] == "服务器"
    assert windows_sheet["object_category"] == "Windows"
    assert windows_sheet["is_server"] is True

    items_resp = client.get("/api/v1/assessment-templates/items", params={"workbook_id": workbook_id})
    assert items_resp.status_code == 200
    items = items_resp.json()["data"]["items"]
    assert len(items) == 4

    firewall_identity = next(item for item in items if item["sheet_name"] == "外联防火墙A" and item["item_code"] == "A-01")
    assert firewall_identity["standard_type"] == "安全通信网络"
    assert firewall_identity["control_point"] == "身份鉴别"
    assert firewall_identity["item_text"] == "a）应对管理员身份进行鉴别"
    assert firewall_identity["record_template"] == "经现场核查，管理员账号已启用口令认证。"
    assert firewall_identity["default_compliance_result"] == "符合"
    assert firewall_identity["weight"] == 1.0
    assert firewall_identity["object_type"] == "安全设备"
    assert firewall_identity["page_types_json"] == ["password_policy"]
    assert firewall_identity["raw_row_json"]["alternative_templates"] == ["样例A1", "样例A2", "样例A3"]

    firewall_access = next(item for item in items if item["sheet_name"] == "外联防火墙A" and item["item_code"] == "A-02")
    assert firewall_access["standard_type"] == "安全通信网络"
    assert firewall_access["control_point"] == "访问控制"
    assert firewall_access["page_types_json"] == ["access_control_policy"]

    filter_resp = client.get(
        "/api/v1/assessment-templates/items",
        params={
            "workbook_id": workbook_id,
            "sheet_name": "核心交换机",
            "object_type": "网络设备",
            "object_category": "交换机",
            "control_point": "安全审计",
            "item_code": "B-01",
            "keyword": "关键操作",
            "page_type": "audit_log",
        },
    )
    assert filter_resp.status_code == 200
    filtered = filter_resp.json()["data"]["items"]
    assert len(filtered) == 1
    assert filtered[0]["sheet_name"] == "核心交换机"
    assert filtered[0]["item_text"] == "b）应记录关键操作"

    acceptance_resp = client.get(
        "/api/v1/assessment-templates/items",
        params={"workbook_id": workbook_id, "sheet_name": "Windows服务器", "control_point": "访问控制", "keyword": "账户权限", "page_type": "access_control_policy"},
    )
    assert acceptance_resp.status_code == 200
    acceptance_items = acceptance_resp.json()["data"]["items"]
    assert len(acceptance_items) == 1
    assert acceptance_items[0]["item_text"] == "a）应配置账户权限"


def test_update_and_delete_assessment_template_workbook(client, db_session):
    import_assessment_template(client)
    workbook = client.get("/api/v1/assessment-templates").json()["data"]["items"][0]

    update_resp = client.patch(
        f"/api/v1/assessment-templates/{workbook['id']}",
        json={"name": "新模板名", "version": "v2"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["data"]
    assert updated["name"] == "新模板名"
    assert updated["version"] == "v2"

    delete_resp = client.delete(f"/api/v1/assessment-templates/{workbook['id']}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"]["archived"] is False


def test_delete_assessment_template_workbook_requires_force_when_referenced(client, db_session):
    import_assessment_template(client)
    workbook = client.get("/api/v1/assessment-templates").json()["data"]["items"][0]

    project = Project(name="引用项目")
    db_session.add(project)
    db_session.flush()
    asset = Asset(
        project_id=project.id,
        asset_kind="test_object",
        category="host",
        category_label="主机",
        filename="asset.txt",
        relative_path=f"assets/{project.id}/asset.txt",
    )
    db_session.add(asset)
    db_session.flush()
    db_session.add(
        ProjectAssessmentTable(
            project_id=project.id,
            asset_id=asset.id,
            source_workbook_id=workbook["id"],
            name="项目测评表",
            status="draft",
            item_count=0,
        )
    )
    db_session.commit()

    resp = client.delete(f"/api/v1/assessment-templates/{workbook['id']}")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "TEMPLATE_WORKBOOK_IN_USE"

    force_resp = client.delete(f"/api/v1/assessment-templates/{workbook['id']}", params={"force": True})
    assert force_resp.status_code == 200
    data = force_resp.json()["data"]
    assert data["archived"] is True
    assert data["referenced_project_table_count"] == 1


def test_update_and_delete_assessment_template_item(client):
    import_assessment_template(client)
    item = client.get("/api/v1/assessment-templates/items").json()["data"]["items"][0]

    update_resp = client.patch(
        f"/api/v1/assessment-template-items/{item['id']}",
        json={"control_point": "新的控制点", "item_text": "新的测评项"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["data"]
    assert updated["control_point"] == "新的控制点"
    assert updated["item_text"] == "新的测评项"

    delete_resp = client.delete(f"/api/v1/assessment-template-items/{item['id']}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"]["id"] == item["id"]


def test_import_assessment_templates_rejects_non_xlsx(client):
    resp = client.post(
        "/api/v1/assessment-templates/import-excel",
        files={"file": ("broken.csv", b"not-excel", "text/csv")},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "ASSESSMENT_TEMPLATE_INVALID_TYPE"


def test_import_assessment_templates_rejects_missing_header(client):
    resp = client.post(
        "/api/v1/assessment-templates/import-excel",
        files={"file": ("broken.xlsx", build_assessment_template_excel_without_header(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "ASSESSMENT_TEMPLATE_HEADER_NOT_FOUND"
