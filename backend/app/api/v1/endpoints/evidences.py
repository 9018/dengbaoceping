import json
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse, list_response, success_response
from app.schemas.evidence import EvidenceExtractRequest, EvidenceOCRRequest, EvidenceUploadData
from app.services.evidence_service import EvidenceService
from app.services.field_extraction_service import FieldExtractionService
from app.services.ocr_service import OCRService

router = APIRouter(tags=["evidences"])
service = EvidenceService()
ocr_service = OCRService()
field_service = FieldExtractionService()


@router.get("/projects/{project_id}/evidences", response_model=ApiResponse)
def list_evidences(project_id: str, db: Session = Depends(get_db)):
    return list_response(service.list_project_evidences(db, project_id))


@router.post("/projects/{project_id}/evidences/upload", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def upload_evidence(
    project_id: str,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    evidence_type: str = Form(default="uploaded_file"),
    summary: str | None = Form(default=None),
    text_content: str | None = Form(default=None),
    device: str | None = Form(default=None),
    ports_json: str | None = Form(default=None),
    evidence_time: str | None = Form(default=None),
    tags_json: str | None = Form(default=None),
    source_ref: str | None = Form(default=None),
    category: str = Form(default="evidence"),
    category_label: str = Form(default="证据文件"),
    db: Session = Depends(get_db),
):
    payload = EvidenceUploadData(
        title=title,
        evidence_type=evidence_type,
        summary=summary,
        text_content=text_content,
        device=device,
        ports_json=json.loads(ports_json) if ports_json else None,
        evidence_time=datetime.fromisoformat(evidence_time) if evidence_time else None,
        tags_json=json.loads(tags_json) if tags_json else None,
        source_ref=source_ref,
        category=category,
        category_label=category_label,
    )
    evidence = service.upload_project_evidence(db, project_id, file, payload)
    return success_response(evidence, "证据上传成功")


@router.get("/evidences/{evidence_id}", response_model=ApiResponse)
def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    return success_response(service.get_evidence(db, evidence_id))


@router.post("/evidences/{evidence_id}/ocr", response_model=ApiResponse)
def run_ocr(evidence_id: str, payload: EvidenceOCRRequest, db: Session = Depends(get_db)):
    evidence = ocr_service.run_ocr(db, evidence_id, payload.sample_id)
    return success_response(evidence, "OCR执行成功")


@router.get("/evidences/{evidence_id}/ocr-result", response_model=ApiResponse)
def get_ocr_result(evidence_id: str, db: Session = Depends(get_db)):
    return success_response(ocr_service.get_ocr_result(db, evidence_id))


@router.post("/evidences/{evidence_id}/extract-fields", response_model=ApiResponse)
def extract_fields(evidence_id: str, payload: EvidenceExtractRequest, db: Session = Depends(get_db)):
    fields = field_service.extract_fields(db, evidence_id, payload.template_code)
    return list_response(fields, "字段抽取完成")


@router.get("/evidences/{evidence_id}/fields", response_model=ApiResponse)
def list_fields(evidence_id: str, db: Session = Depends(get_db)):
    return list_response(field_service.list_fields(db, evidence_id))


@router.delete("/evidences/{evidence_id}", response_model=ApiResponse)
def delete_evidence(evidence_id: str, db: Session = Depends(get_db)):
    service.delete_evidence(db, evidence_id)
    return success_response(message="证据已删除")
