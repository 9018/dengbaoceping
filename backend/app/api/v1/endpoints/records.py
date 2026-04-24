from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.audit import AuditLogRead
from app.schemas.common import ApiResponse, list_response, success_response
from app.schemas.record import RecordGenerateRequest, RecordRead, RecordReviewRequest, RecordUpdateRequest
from app.services.record_service import RecordService

router = APIRouter(tags=["records"])
service = RecordService()


@router.post("/projects/{project_id}/records/generate", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def generate_record(project_id: str, payload: RecordGenerateRequest, db: Session = Depends(get_db)):
    record = service.generate_record(
        db,
        project_id,
        payload.evidence_id,
        payload.device_type_override,
        payload.force_regenerate,
    )
    return success_response(RecordRead.model_validate(record), "测评记录生成成功")


@router.get("/projects/{project_id}/records", response_model=ApiResponse)
def list_records(project_id: str, db: Session = Depends(get_db)):
    records = [RecordRead.model_validate(item) for item in service.list_project_records(db, project_id)]
    return list_response(records, "测评记录列表获取成功")


@router.get("/records/{record_id}", response_model=ApiResponse)
def get_record(record_id: str, db: Session = Depends(get_db)):
    record = service.get_record(db, record_id)
    return success_response(RecordRead.model_validate(record), "测评记录详情获取成功")


@router.put("/records/{record_id}", response_model=ApiResponse)
def update_record(record_id: str, payload: RecordUpdateRequest, db: Session = Depends(get_db)):
    record = service.update_record(db, record_id, payload.model_dump())
    return success_response(RecordRead.model_validate(record), "测评记录更新成功")


@router.post("/records/{record_id}/review", response_model=ApiResponse)
def review_record(record_id: str, payload: RecordReviewRequest, db: Session = Depends(get_db)):
    record = service.review_record(db, record_id, payload.model_dump())
    return success_response(RecordRead.model_validate(record), "测评记录复核成功")


@router.get("/records/{record_id}/audit-logs", response_model=ApiResponse)
def list_record_audit_logs(record_id: str, db: Session = Depends(get_db)):
    logs = [AuditLogRead.model_validate(item) for item in service.list_record_audit_logs(db, record_id)]
    return list_response(logs, "测评记录审计日志获取成功")
