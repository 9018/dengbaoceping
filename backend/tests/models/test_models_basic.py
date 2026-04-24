from sqlalchemy.orm import Session

from app.models.evaluation_record import EvaluationRecord, EvaluationRecordEvidence
from app.models.evidence import Evidence
from app.models.export_job import ExportJob
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
