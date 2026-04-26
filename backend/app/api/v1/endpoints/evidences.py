import json
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse, list_response, success_response
from app.schemas.evidence import (
    EvidenceClassifyPageRead,
    EvidenceClassifyPageRequest,
    EvidenceConfirmAssetRequest,
    EvidenceConfirmGuidanceRequest,
    EvidenceExtractRequest,
    EvidenceHistoryMatchRead,
    EvidenceHistoryMatchRequest,
    EvidenceMatchAssetRequest,
    EvidenceMatchGuidanceRequest,
    EvidenceOCRRequest,
    EvidenceRead,
    EvidenceTemplateItemMatchRead,
    EvidenceTemplateItemMatchRequest,
    EvidenceUploadData,
)
from app.services.asset_match_service import AssetMatchService
from app.services.evidence_service import EvidenceService
from app.services.evidence_to_history_match_service import EvidenceToHistoryMatchService
from app.services.field_extraction_service import FieldExtractionService
from app.services.guidance_match_service import GuidanceMatchService
from app.services.ocr_service import OCRService
from app.services.template_item_match_service import TemplateItemMatchService

router = APIRouter(tags=["evidences"])
service = EvidenceService()
ocr_service = OCRService()
field_service = FieldExtractionService()
asset_match_service = AssetMatchService()
guidance_match_service = GuidanceMatchService()
history_match_service = EvidenceToHistoryMatchService()
template_item_match_service = TemplateItemMatchService()


def serialize_evidence(evidence):
    return EvidenceRead.model_validate(evidence)


@router.get("/projects/{project_id}/evidences", response_model=ApiResponse)
def list_evidences(project_id: str, db: Session = Depends(get_db)):
    evidences = service.list_project_evidences(db, project_id)
    return list_response([serialize_evidence(item) for item in evidences])


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
    return success_response(serialize_evidence(evidence), "证据上传成功")


@router.get("/evidences/{evidence_id}", response_model=ApiResponse)
def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    return success_response(serialize_evidence(service.get_evidence(db, evidence_id)))


@router.post("/evidences/{evidence_id}/ocr", response_model=ApiResponse)
def run_ocr(evidence_id: str, payload: EvidenceOCRRequest, db: Session = Depends(get_db)):
    evidence = ocr_service.run_ocr(db, evidence_id, payload.sample_id)
    return success_response(serialize_evidence(evidence), "OCR执行成功")


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


@router.post("/evidences/{evidence_id}/match-asset", response_model=ApiResponse)
def match_asset(evidence_id: str, payload: EvidenceMatchAssetRequest, db: Session = Depends(get_db)):
    evidence = asset_match_service.match_asset(db, evidence_id, payload.force)
    return success_response(serialize_evidence(evidence), "测试对象匹配完成")


@router.post("/evidences/{evidence_id}/confirm-asset", response_model=ApiResponse)
def confirm_asset(evidence_id: str, payload: EvidenceConfirmAssetRequest, db: Session = Depends(get_db)):
    evidence = asset_match_service.confirm_asset(db, evidence_id, payload.asset_id)
    return success_response(serialize_evidence(evidence), "测试对象绑定成功")


@router.post("/evidences/{evidence_id}/match-guidance", response_model=ApiResponse)
def match_guidance(evidence_id: str, payload: EvidenceMatchGuidanceRequest, db: Session = Depends(get_db)):
    evidence = guidance_match_service.match_guidance(db, evidence_id, payload.force)
    return success_response(serialize_evidence(evidence), "指导书匹配完成")


@router.post("/evidences/{evidence_id}/confirm-guidance", response_model=ApiResponse)
def confirm_guidance(evidence_id: str, payload: EvidenceConfirmGuidanceRequest, db: Session = Depends(get_db)):
    evidence = guidance_match_service.confirm_guidance(db, evidence_id, payload.guidance_id)
    return success_response(serialize_evidence(evidence), "指导书绑定成功")


@router.post("/evidences/{evidence_id}/classify-page", response_model=ApiResponse)
def classify_evidence_page(evidence_id: str, payload: EvidenceClassifyPageRequest, db: Session = Depends(get_db)):
    result = history_match_service.classify_page(
        db,
        evidence_id,
        ocr_text=payload.ocr_text,
        extracted_fields=payload.extracted_fields,
    )
    return success_response(EvidenceClassifyPageRead.model_validate(result), "页面类型识别完成")


@router.post("/evidences/{evidence_id}/match-history", response_model=ApiResponse)
def match_evidence_history(evidence_id: str, payload: EvidenceHistoryMatchRequest, db: Session = Depends(get_db)):
    result = history_match_service.match(
        db,
        evidence_id,
        ocr_text=payload.ocr_text,
        page_type=payload.page_type,
        asset_type=payload.asset_type,
        extracted_fields=payload.extracted_fields,
    )
    return success_response(EvidenceHistoryMatchRead.model_validate(result), "历史记录匹配完成")


@router.post("/evidences/{evidence_id}/match-template-item", response_model=ApiResponse)
def match_template_item(evidence_id: str, payload: EvidenceTemplateItemMatchRequest, db: Session = Depends(get_db)):
    result = template_item_match_service.match(
        db,
        evidence_id,
        ocr_text=payload.ocr_text,
        page_type=payload.page_type,
        asset_type=payload.asset_type,
        extracted_fields=payload.extracted_fields,
        evidence_facts=payload.evidence_facts,
    )
    return success_response(EvidenceTemplateItemMatchRead.model_validate(result), "结果记录模板匹配完成")


@router.delete("/evidences/{evidence_id}", response_model=ApiResponse)
def delete_evidence(evidence_id: str, db: Session = Depends(get_db)):
    service.delete_evidence(db, evidence_id)
    return success_response(message="证据已删除")
