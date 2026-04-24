from types import SimpleNamespace

import pytest
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException
from app.schemas.evidence import EvidenceUploadData
from app.services.evidence_service import EvidenceService
from app.services.export_service import ExportService
from app.services.field_extraction_service import FieldExtractionService
from app.services.project_service import ProjectService
from app.services.record_service import RecordService


def create_project(service: ProjectService, db: Session, code: str = "PJT-SVC"):
    payload = SimpleNamespace(
        code=code,
        name="服务测试项目",
        project_type="等级保护测评",
        status="draft",
        description=None,
        model_dump=lambda: {
            "code": code,
            "name": "服务测试项目",
            "project_type": "等级保护测评",
            "status": "draft",
            "description": None,
        },
    )
    return service.create_project(db, payload=payload)


def upload_evidence(service: EvidenceService, db: Session, project_id: str, filename: str = "sample.txt"):
    with open(__file__, "rb") as fh:
        upload = UploadFile(filename=filename, file=fh)
        payload = EvidenceUploadData(title="样例证据", evidence_type="screenshot", summary="服务测试", device="FW-01")
        return service.upload_project_evidence(db, project_id, upload, payload)


def test_field_extraction_service_requires_ocr_text(db_session):
    project_service = ProjectService()
    evidence_service = EvidenceService()
    field_service = FieldExtractionService()

    project = create_project(project_service, db_session)
    evidence = upload_evidence(evidence_service, db_session, project.id)

    with pytest.raises(BadRequestException) as exc:
        field_service.extract_fields(db_session, evidence.id, "security_device_basic")
    assert exc.value.code == "OCR_TEXT_NOT_FOUND"


def test_record_service_reuses_existing_record_without_force(db_session):
    project_service = ProjectService()
    evidence_service = EvidenceService()
    field_service = FieldExtractionService()
    record_service = RecordService()

    project = create_project(project_service, db_session, code="PJT-REC-SVC")
    evidence = upload_evidence(evidence_service, db_session, project.id)
    evidence.text_content = "设备名称: FW-01\n设备IP: 10.0.0.1\n安全策略状态: 已启用\n"
    db_session.commit()
    field_service.extract_fields(db_session, evidence.id, "security_device_basic")

    first = record_service.generate_record(db_session, project.id, evidence.id)
    second = record_service.generate_record(db_session, project.id, evidence.id)
    assert first.id == second.id


def test_record_service_rejects_invalid_status_transition(db_session):
    record_service = RecordService()
    with pytest.raises(BadRequestException) as exc:
        record_service._validate_transition("reviewed", "exported")
    assert exc.value.code == "INVALID_RECORD_STATUS_TRANSITION"


def test_export_service_renders_empty_project_group(db_session):
    export_service = ExportService()
    content = export_service._render_txt("空项目", [])
    assert "项目：空项目" in content
    assert "设备：未分组" in content
    assert "无测评记录" in content
