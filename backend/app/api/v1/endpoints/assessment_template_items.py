from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.assessment_template import (
    AssessmentTemplateItemRead,
    AssessmentTemplateItemUpdate,
    TemplateGuidebookLinkRead,
    TemplateGuidebookLinkResultRead,
    TemplateHistoryLinkRead,
    TemplateHistoryLinkResultRead,
)
from app.schemas.common import ApiResponse, list_response, success_response
from app.services.assessment_template_service import AssessmentTemplateService
from app.services.template_guidebook_link_service import TemplateGuidebookLinkService
from app.services.template_history_link_service import TemplateHistoryLinkService

router = APIRouter(prefix="/assessment-template-items", tags=["assessment-template-items"])
guidebook_service = TemplateGuidebookLinkService()
history_service = TemplateHistoryLinkService()
service = AssessmentTemplateService()


@router.patch("/{item_id}", response_model=ApiResponse)
def update_assessment_template_item(
    item_id: str,
    payload: AssessmentTemplateItemUpdate,
    db: Session = Depends(get_db),
):
    item = service.update_item(db, item_id, **payload.model_dump())
    return success_response(AssessmentTemplateItemRead.model_validate(item), "模板项更新成功")


@router.delete("/{item_id}", response_model=ApiResponse)
def delete_assessment_template_item(item_id: str, db: Session = Depends(get_db)):
    result = service.delete_item(db, item_id)
    return success_response(result, "模板项删除成功")


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
