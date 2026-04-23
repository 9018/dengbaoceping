from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse, success_response
from app.schemas.field import ExtractedFieldRead, FieldReviewRequest, FieldUpdateRequest
from app.services.field_review_service import FieldReviewService

router = APIRouter(tags=["fields"])
service = FieldReviewService()


@router.put("/fields/{field_id}", response_model=ApiResponse)
def update_field(field_id: str, payload: FieldUpdateRequest, db: Session = Depends(get_db)):
    field = service.update_field(db, field_id, payload.model_dump())
    return success_response(ExtractedFieldRead.model_validate(field), "字段更新成功")


@router.post("/fields/{field_id}/review", response_model=ApiResponse)
def review_field(field_id: str, payload: FieldReviewRequest, db: Session = Depends(get_db)):
    field = service.review_field(db, field_id, payload.model_dump())
    return success_response(ExtractedFieldRead.model_validate(field), "字段复核成功")
