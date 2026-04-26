from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.assessment_template import (
    TemplateGuidebookLinkRead,
    TemplateGuidebookLinkResultRead,
    TemplateHistoryLinkRead,
    TemplateHistoryLinkResultRead,
)
from app.schemas.common import ApiResponse, list_response, success_response
from app.services.template_guidebook_link_service import TemplateGuidebookLinkService
from app.services.template_history_link_service import TemplateHistoryLinkService

router = APIRouter(prefix="/assessment-template-items", tags=["assessment-template-items"])
guidebook_service = TemplateGuidebookLinkService()
history_service = TemplateHistoryLinkService()


@router.post("/{item_id}/link-guidebook", response_model=ApiResponse)
def link_template_item_guidebook(item_id: str, db: Session = Depends(get_db)):
    result = guidebook_service.link_guidebook(db, item_id)
    return success_response(TemplateGuidebookLinkResultRead.model_validate(result), "模板项关联指导书成功")


@router.get("/{item_id}/guidebook-links", response_model=ApiResponse)
def list_template_item_guidebook_links(item_id: str, db: Session = Depends(get_db)):
    result = guidebook_service.list_guidebook_links(db, item_id)
    return list_response([TemplateGuidebookLinkRead.model_validate(item) for item in result], "模板项关联指导书列表获取成功")


@router.post("/{item_id}/link-history", response_model=ApiResponse)
def link_template_item_history(item_id: str, db: Session = Depends(get_db)):
    result = history_service.link_history(db, item_id)
    return success_response(TemplateHistoryLinkResultRead.model_validate(result), "模板项关联历史记录成功")


@router.get("/{item_id}/history-links", response_model=ApiResponse)
def list_template_item_history_links(
    item_id: str,
    compliance_result: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    result = history_service.list_history_links(db, item_id, compliance_result)
    return list_response([TemplateHistoryLinkRead.model_validate(item) for item in result], "模板项关联历史记录列表获取成功")
