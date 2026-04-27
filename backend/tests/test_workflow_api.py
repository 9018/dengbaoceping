from tests.test_evidences_api import create_project, upload_evidence

from app.models.asset import Asset
from app.models.assessment_template import AssessmentTemplateItem, AssessmentTemplateSheet, AssessmentTemplateWorkbook
from app.models.evidence import Evidence
from app.models.evidence_fact import EvidenceFact
from app.models.guidance_item import GuidanceItem
from app.models.history_record import HistoryRecord
from app.models.project_assessment_table import ProjectAssessmentItem, ProjectAssessmentTable


def create_test_object_asset(db_session, project_id: str, *, filename: str = "FW-01", category: str = "firewall") -> Asset:
    asset = Asset(
        project_id=project_id,
        asset_kind="test_object",
        category=category,
        category_label="防火墙",
        filename=filename,
        relative_path=f"assets/{filename}.txt",
        ingest_status="pending",
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def create_template_workbook_with_item(db_session) -> tuple[AssessmentTemplateWorkbook, AssessmentTemplateItem]:
    workbook = AssessmentTemplateWorkbook(
        source_file="template.xlsx",
        source_file_hash="hash-template",
        file_size=1,
        name="模板A",
        version="v1",
        sheet_count=1,
        item_count=1,
        is_archived=False,
    )
    db_session.add(workbook)
    db_session.flush()

    sheet = AssessmentTemplateSheet(
        workbook_id=workbook.id,
        sheet_name="外联防火墙A",
        object_type="device",
        object_category="firewall",
        row_count=1,
    )
    db_session.add(sheet)
    db_session.flush()

    item = AssessmentTemplateItem(
        workbook_id=workbook.id,
        sheet_id=sheet.id,
        sheet_name=sheet.sheet_name,
        row_index=1,
        control_point="边界访问控制",
        item_text="应限制非授权访问",
        item_code="A-01",
        object_type="device",
        object_category="firewall",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(workbook)
    db_session.refresh(item)
    return workbook, item


def create_guidance_item(db_session) -> GuidanceItem:
    item = GuidanceItem(
        guidance_code="guide-001",
        source_file="md/指导书.md",
        source_file_hash="hash-guidance",
        section_path="网络安全/边界防护",
        section_title="边界防护",
        level1="网络安全",
        level2="边界防护",
        raw_markdown="内容",
        plain_text="内容",
        keywords_json=["边界"],
        check_points_json=[],
        evidence_requirements_json=[],
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


def create_history_record(db_session) -> HistoryRecord:
    record = HistoryRecord(
        source_file="history.xlsx",
        source_file_hash="hash-history",
        sheet_name="外联防火墙A",
        asset_name="FW-01",
        asset_type="firewall",
        control_point="边界访问控制",
        item_text="应限制非授权访问",
        evaluation_item="应限制非授权访问",
        record_text="已配置访问控制策略",
        raw_text="已配置访问控制策略",
        compliance_result="符合",
        compliance_status="符合",
        row_index=1,
        keywords_json=["访问控制"],
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


def create_project_table_with_item(db_session, project_id: str, asset_id: str, source_template_item_id: str | None = None) -> tuple[ProjectAssessmentTable, ProjectAssessmentItem]:
    table = ProjectAssessmentTable(
        project_id=project_id,
        asset_id=asset_id,
        source_workbook_id=None,
        name="项目测评表",
        status="draft",
        item_count=1,
    )
    db_session.add(table)
    db_session.flush()

    item = ProjectAssessmentItem(
        table_id=table.id,
        project_id=project_id,
        asset_id=asset_id,
        source_template_item_id=source_template_item_id,
        sheet_name="外联防火墙A",
        row_index=1,
        control_point="边界访问控制",
        item_text="应限制非授权访问",
        item_code="A-01",
        object_type="device",
        object_category="firewall",
        status="pending",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(table)
    db_session.refresh(item)
    return table, item


def create_evidence_fact(db_session, project_id: str, evidence_id: str, asset_id: str | None = None, item_id: str | None = None) -> EvidenceFact:
    fact = EvidenceFact(
        project_id=project_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        project_assessment_item_id=item_id,
        page_type="access_control_policy",
        fact_group="policy",
        fact_key="action",
        fact_name="动作",
        raw_value="permit",
        normalized_value="permit",
        source_text="动作：permit",
        status="identified",
    )
    db_session.add(fact)
    db_session.commit()
    db_session.refresh(fact)
    return fact


def get_workflow_status(client, project_id: str) -> dict:
    resp = client.get(f"/api/v1/projects/{project_id}/workflow/status")
    assert resp.status_code == 200
    return resp.json()["data"]


def get_next_action(client, project_id: str) -> dict:
    resp = client.get(f"/api/v1/projects/{project_id}/assessment-next-action")
    assert resp.status_code == 200
    return resp.json()["data"]


def test_project_workflow_status_requires_global_template(client):
    project_id = create_project(client)

    status = get_workflow_status(client, project_id)

    assert status["status"] == "global_template_missing"
    assert status["canNext"] is False
    assert status["next_action"]["step_key"] == "setup"
    assert status["next_action"]["route"] == "/setup-wizard"


def test_project_workflow_status_requires_guidance_after_template(db_session, client):
    project_id = create_project(client)
    create_template_workbook_with_item(db_session)

    status = get_workflow_status(client, project_id)

    assert status["status"] == "guidance_missing"
    assert status["next_action"]["step_key"] == "setup"


def test_project_workflow_status_requires_history_after_guidance(db_session, client):
    project_id = create_project(client)
    create_template_workbook_with_item(db_session)
    create_guidance_item(db_session)

    status = get_workflow_status(client, project_id)

    assert status["status"] == "history_missing"
    assert status["next_action"]["step_key"] == "setup"


def test_project_workflow_status_requires_asset_after_global_libraries(db_session, client):
    project_id = create_project(client)
    create_template_workbook_with_item(db_session)
    create_guidance_item(db_session)
    create_history_record(db_session)

    status = get_workflow_status(client, project_id)

    assert status["status"] == "asset_missing"
    assert status["canNext"] is True
    assert status["next_action"]["step_key"] == "asset"
    assert status["next_action"]["route"] == f"/projects/{project_id}/assessment-wizard"


def test_project_workflow_status_requires_table_when_asset_exists(db_session, client):
    project_id = create_project(client)
    workbook, _ = create_template_workbook_with_item(db_session)
    create_guidance_item(db_session)
    create_history_record(db_session)
    asset = create_test_object_asset(db_session, project_id)

    status = get_workflow_status(client, project_id)

    assert workbook.id
    assert status["status"] == "table_missing"
    assert status["next_action"]["asset_id"] == asset.id
    assert status["next_action"]["step_key"] == "table"


def test_project_workflow_status_requires_evidence_when_table_exists(db_session, client):
    project_id = create_project(client)
    _, template_item = create_template_workbook_with_item(db_session)
    create_guidance_item(db_session)
    create_history_record(db_session)
    asset = create_test_object_asset(db_session, project_id)
    table, _ = create_project_table_with_item(db_session, project_id, asset.id, source_template_item_id=template_item.id)

    status = get_workflow_status(client, project_id)

    assert table.id
    assert status["status"] == "evidence_missing"
    assert status["next_action"]["step_key"] == "evidence"
    assert status["stats"]["table_count"] == 1
    assert status["stats"]["item_count"] == 1


def test_project_workflow_status_requires_ocr_when_evidence_has_no_text(db_session, client):
    project_id = create_project(client)
    _, template_item = create_template_workbook_with_item(db_session)
    create_guidance_item(db_session)
    create_history_record(db_session)
    asset = create_test_object_asset(db_session, project_id)
    create_project_table_with_item(db_session, project_id, asset.id, source_template_item_id=template_item.id)
    evidence_id = upload_evidence(client, project_id, "pending-ocr.txt")

    status = get_workflow_status(client, project_id)

    assert status["status"] == "ocr_pending"
    assert status["next_action"]["evidence_id"] == evidence_id
    assert status["next_action"]["step_key"] == "ocr"


def test_project_workflow_status_treats_failed_with_text_as_facts_missing(db_session, client):
    project_id = create_project(client)
    _, template_item = create_template_workbook_with_item(db_session)
    create_guidance_item(db_session)
    create_history_record(db_session)
    asset = create_test_object_asset(db_session, project_id)
    create_project_table_with_item(db_session, project_id, asset.id, source_template_item_id=template_item.id)
    evidence_id = upload_evidence(client, project_id, "warning-ocr.txt")

    evidence = db_session.get(Evidence, evidence_id)
    evidence.ocr_status = "failed"
    evidence.text_content = "补录文本可用"
    evidence.ocr_result_json = {"status": "failed", "full_text": "补录文本可用"}
    db_session.add(evidence)
    db_session.commit()

    status = get_workflow_status(client, project_id)

    assert status["status"] == "facts_missing"
    assert status["next_action"]["evidence_id"] == evidence_id
    assert status["next_action"]["step_key"] == "facts"


def test_project_workflow_status_requires_item_match_after_facts(db_session, client):
    project_id = create_project(client)
    _, template_item = create_template_workbook_with_item(db_session)
    create_guidance_item(db_session)
    create_history_record(db_session)
    asset = create_test_object_asset(db_session, project_id)
    _, project_item = create_project_table_with_item(db_session, project_id, asset.id, source_template_item_id=template_item.id)
    evidence_id = upload_evidence(client, project_id, "facts-ready.txt")

    evidence = db_session.get(Evidence, evidence_id)
    evidence.ocr_status = "completed"
    evidence.text_content = "动作：permit"
    evidence.ocr_result_json = {"status": "completed", "full_text": "动作：permit"}
    db_session.add(evidence)
    db_session.commit()

    create_evidence_fact(db_session, project_id, evidence_id, asset_id=asset.id)

    status = get_workflow_status(client, project_id)
    next_action = get_next_action(client, project_id)

    assert status["status"] == "item_match_missing"
    assert status["next_action"]["item_id"] == project_item.id
    assert status["next_action"]["evidence_id"] == evidence_id
    assert next_action["stage"] == "item_match_missing"
    assert next_action["step_key"] == "match"


def test_project_workflow_status_requires_draft_after_match(db_session, client):
    project_id = create_project(client)
    _, template_item = create_template_workbook_with_item(db_session)
    create_guidance_item(db_session)
    create_history_record(db_session)
    asset = create_test_object_asset(db_session, project_id)
    _, project_item = create_project_table_with_item(db_session, project_id, asset.id, source_template_item_id=template_item.id)
    evidence_id = upload_evidence(client, project_id, "matched.txt")

    evidence = db_session.get(Evidence, evidence_id)
    evidence.ocr_status = "completed"
    evidence.text_content = "动作：permit"
    evidence.ocr_result_json = {"status": "completed", "full_text": "动作：permit"}
    db_session.add(evidence)
    db_session.commit()

    create_evidence_fact(db_session, project_id, evidence_id, asset_id=asset.id)

    project_item.evidence_ids_json = [evidence_id]
    db_session.add(project_item)
    db_session.commit()

    status = get_workflow_status(client, project_id)

    assert status["status"] == "draft_missing"
    assert status["next_action"]["item_id"] == project_item.id
    assert status["next_action"]["evidence_id"] == evidence_id
    assert status["next_action"]["step_key"] == "draft"


def test_project_workflow_status_requires_confirm_after_draft(db_session, client):
    project_id = create_project(client)
    _, template_item = create_template_workbook_with_item(db_session)
    create_guidance_item(db_session)
    create_history_record(db_session)
    asset = create_test_object_asset(db_session, project_id)
    _, project_item = create_project_table_with_item(db_session, project_id, asset.id, source_template_item_id=template_item.id)
    evidence_id = upload_evidence(client, project_id, "drafted.txt")

    evidence = db_session.get(Evidence, evidence_id)
    evidence.ocr_status = "completed"
    evidence.text_content = "动作：permit"
    evidence.ocr_result_json = {"status": "completed", "full_text": "动作：permit"}
    db_session.add(evidence)

    create_evidence_fact(db_session, project_id, evidence_id, asset_id=asset.id)

    project_item.evidence_ids_json = [evidence_id]
    project_item.draft_record_text = "经核查，已配置访问控制策略"
    project_item.draft_compliance_result = "符合"
    project_item.status = "drafted"
    db_session.add(project_item)
    db_session.commit()

    status = get_workflow_status(client, project_id)

    assert status["status"] == "confirm_missing"
    assert status["next_action"]["item_id"] == project_item.id
    assert status["next_action"]["step_key"] == "confirm"


def test_project_workflow_status_completed_after_item_confirmed(db_session, client):
    project_id = create_project(client)
    _, template_item = create_template_workbook_with_item(db_session)
    create_guidance_item(db_session)
    create_history_record(db_session)
    asset = create_test_object_asset(db_session, project_id)
    _, project_item = create_project_table_with_item(db_session, project_id, asset.id, source_template_item_id=template_item.id)
    evidence_id = upload_evidence(client, project_id, "confirmed.txt")

    evidence = db_session.get(Evidence, evidence_id)
    evidence.ocr_status = "completed_with_warning"
    evidence.text_content = "动作：permit"
    evidence.ocr_result_json = {"status": "failed", "full_text": "动作：permit"}
    db_session.add(evidence)

    create_evidence_fact(db_session, project_id, evidence_id, asset_id=asset.id, item_id=project_item.id)

    project_item.evidence_ids_json = [evidence_id]
    project_item.draft_record_text = "经核查，已配置访问控制策略"
    project_item.draft_compliance_result = "符合"
    project_item.final_record_text = "经核查，已配置访问控制策略"
    project_item.final_compliance_result = "符合"
    project_item.status = "confirmed"
    db_session.add(project_item)
    db_session.commit()

    status = get_workflow_status(client, project_id)
    next_action = get_next_action(client, project_id)

    assert status["status"] == "completed"
    assert status["summary"] == "项目测评流程已完成，可进入导出中心"
    assert status["next_action"]["step_key"] == "export"
    assert status["stats"]["ocr_completed_count"] == 1
    assert status["stats"]["fact_count"] == 1
    assert status["stats"]["matched_item_count"] == 1
    assert status["stats"]["drafted_item_count"] == 1
    assert status["stats"]["confirmed_item_count"] == 1
    assert status["stats"]["pending_item_count"] == 0
    assert next_action["stage"] == "completed"
