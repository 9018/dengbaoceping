from tests.history_excel_utils import build_final_assessment_excel


def test_import_project_template_excel_api(client, db_session):
    create_resp = client.post(
        "/api/v1/projects",
        json={"code": "PJT-TPL", "name": "模板项目", "project_type": "等级保护测评", "status": "draft"},
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["data"]["id"]

    resp = client.post(
        f"/api/v1/projects/{project_id}/templates/import-reference",
        files={"file": ("reference.xlsx", build_final_assessment_excel(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["sheet_count"] == 1
    assert data["sheet_names"] == ["出口防火墙-A"]
    assert data["imported_count"] == 2
    assert data["skipped_count"] == 0

    from app.models.evaluation_item import EvaluationItem
    from app.models.template import Template

    template = db_session.query(Template).filter(Template.project_id == project_id, Template.is_active.is_(True)).one()
    assert template.template_type == "project_record_reference"
    assert template.source_asset is not None
    assert template.source_asset.asset_kind == "project_template_file"

    rows = db_session.query(EvaluationItem).filter(EvaluationItem.template_id == template.id).order_by(EvaluationItem.sort_order.asc()).all()
    assert len(rows) == 2
    assert rows[0].source_sheet_name == "出口防火墙-A"
    assert rows[0].extension_standard == "安全通信网络"
    assert rows[0].control_point == "边界访问控制"
    assert rows[0].record_template == "经现场核查，已配置访问控制策略。"
    assert rows[0].default_compliance == "符合"
    assert rows[0].score_weight == 1.0
    assert rows[0].item_no == "A-01"
    assert rows[1].extension_standard == "安全通信网络"
    assert rows[1].control_point == "边界访问控制"
    assert rows[1].item_no == "A-02"

    summary_resp = client.get(f"/api/v1/projects/{project_id}/templates/reference")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()["data"]
    assert summary["template_id"] == template.id
    assert summary["source_file"] == "reference.xlsx"
    assert summary["sheet_count"] == 1
    assert summary["sheet_names"] == ["出口防火墙-A"]
    assert summary["item_count"] == 2


def test_reimport_project_template_deactivates_previous_template(client, db_session):
    create_resp = client.post(
        "/api/v1/projects",
        json={"code": "PJT-TPL-2", "name": "模板项目2", "project_type": "等级保护测评", "status": "draft"},
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["data"]["id"]

    for filename in ("reference-v1.xlsx", "reference-v2.xlsx"):
        resp = client.post(
            f"/api/v1/projects/{project_id}/templates/import-reference",
            files={"file": (filename, build_final_assessment_excel(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 201

    from app.models.template import Template

    templates = (
        db_session.query(Template)
        .filter(Template.project_id == project_id, Template.template_type == "project_record_reference")
        .order_by(Template.created_at.asc())
        .all()
    )
    assert len(templates) == 2
    assert templates[0].is_active is False
    assert templates[1].is_active is True
