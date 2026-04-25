from sqlalchemy.orm import Session

from app.models.evaluation_record import EvaluationRecord, EvaluationRecordEvidence
from app.models.evidence import Evidence
from app.models.export_job import ExportJob
from app.models.guidance_history_link import GuidanceHistoryLink
from app.models.guidance_item import GuidanceItem
from app.models.history_record import HistoryRecord
from app.models.project import Project


def test_project_model_defaults(db_session: Session):
    project = Project(name="模型项目")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    assert project.id
    assert project.status == "draft"
    assert project.project_type == "等级保护测评"


def test_evidence_record_and_export_job_persistence(db_session: Session):
    project = Project(code="PJT-MODEL", name="模型链路项目")
    db_session.add(project)
    db_session.flush()

    evidence = Evidence(project_id=project.id, evidence_type="screenshot", title="证据A", device="FW-01")
    db_session.add(evidence)
    db_session.flush()

    record = EvaluationRecord(project_id=project.id, title="记录A", status="generated", source_type="generated")
    db_session.add(record)
    db_session.flush()

    db_session.add(EvaluationRecordEvidence(evaluation_record_id=record.id, evidence_id=evidence.id, relation_type="source"))
    job = ExportJob(project_id=project.id, format="txt", status="completed", file_name="demo.txt", file_path="/tmp/demo.txt", file_size=12, record_count=1)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(record)
    db_session.refresh(job)

    assert record.evidence_links[0].evidence_id == evidence.id
    assert job.project_id == project.id
    assert job.record_count == 1


def test_guidance_item_persistence(db_session: Session):
    item = GuidanceItem(
        guidance_code="gd-demo-123",
        source_file="md/指导书.md",
        section_path="安全物理环境 / 安全通用要求",
        section_title="安全通用要求",
        level1="安全物理环境",
        level2="安全通用要求",
        level3=None,
        raw_markdown="# 安全物理环境\n## 安全通用要求\n应核查门禁。",
        plain_text="安全物理环境 安全通用要求 应核查门禁。",
        keywords_json=["门禁", "核查"],
        check_points_json=["应核查门禁"],
        evidence_requirements_json=["门禁记录"],
        record_suggestion="应提供门禁记录",
    )

    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert item.id
    assert item.guidance_code == "gd-demo-123"
    assert item.keywords_json == ["门禁", "核查"]


def test_guidance_history_link_persistence(db_session: Session):
    guidance_item = GuidanceItem(
        guidance_code="gd-link-001",
        source_file="md/指导书.md",
        section_path="网络安全 / 边界防护",
        section_title="边界防护",
        level1="网络安全",
        level2="边界防护",
        level3=None,
        raw_markdown="# 网络安全\n## 边界防护\n应核查防火墙访问控制。",
        plain_text="网络安全 边界防护 应核查防火墙访问控制。",
        keywords_json=["防火墙", "访问控制"],
        check_points_json=["应核查防火墙访问控制"],
        evidence_requirements_json=["访问控制策略"],
        record_suggestion="应提供访问控制配置",
    )
    history_record = HistoryRecord(
        source_file="history.xlsx",
        sheet_name="出口防火墙",
        asset_name="出口防火墙",
        asset_type="firewall",
        extension_standard="安全通信网络",
        control_point="边界访问控制",
        evaluation_item="应限制非授权访问",
        record_text="经现场核查，已配置访问控制策略。",
        compliance_status="符合",
        score=1.0,
        item_no="A-01",
        row_index=2,
        keywords_json=["边界访问控制", "访问控制策略"],
    )
    db_session.add_all([guidance_item, history_record])
    db_session.flush()

    link = GuidanceHistoryLink(
        guidance_item_id=guidance_item.id,
        history_record_id=history_record.id,
        match_score=8.5,
        match_reason={"summary": ["控制点命中", "关键词重合"]},
    )
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)

    assert link.id
    assert link.guidance_item_id == guidance_item.id
    assert link.history_record_id == history_record.id
    assert link.match_reason["summary"] == ["控制点命中", "关键词重合"]
