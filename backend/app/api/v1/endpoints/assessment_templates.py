from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.assessment_template import (
    AssessmentTemplateImportRead,
    AssessmentTemplateItemRead,
    AssessmentTemplateSheetRead,
    AssessmentTemplateWorkbookDetailRead,
    AssessmentTemplateWorkbookRead,
    AssessmentTemplateWorkbookUpdate,
)
from app.schemas.common import ApiResponse, paged_response, success_response
from app.services.assessment_template_import_service import AssessmentTemplateImportService
from app.services.assessment_template_service import AssessmentTemplateService

router = APIRouter(prefix="/assessment-templates", tags=["assessment-templates"])
import_service = AssessmentTemplateImportService()
service = AssessmentTemplateService()


@router.post("/import-excel", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def import_assessment_templates_excel(
    file: UploadFile = File(...),
    duplicate_policy: str = Query(default="skip"),
    db: Session = Depends(get_db),
):
    content = await file.read()
    result = import_service.import_excel(db, file.filename or "assessment_template.xlsx", content, duplicate_policy=duplicate_policy)
    return success_response(AssessmentTemplateImportRead.model_validate(result), "测评记录模板导入成功")


@router.get("", response_model=ApiResponse)
def list_assessment_template_workbooks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    include_archived: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    workbooks, total = service.list_workbooks_page(db, page=page, page_size=page_size, include_archived=include_archived)
    return paged_response(
        [AssessmentTemplateWorkbookRead.model_validate(item) for item in workbooks],
        total,
        page,
        page_size,
        "测评记录模板工作簿列表获取成功",
    )


@router.get("/items", response_model=ApiResponse)
def list_assessment_template_items(
    workbook_id: str | None = Query(default=None),
    sheet_name: str | None = Query(default=None),
    object_type: str | None = Query(default=None),
    object_category: str | None = Query(default=None),
    control_point: str | None = Query(default=None),
    item_code: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    page_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    items, total = service.list_items_page(
        db,
        workbook_id=workbook_id,
        sheet_name=sheet_name,
        object_type=object_type,
        object_category=object_category,
        control_point=control_point,
        item_code=item_code,
        keyword=keyword,
        page_type=page_type,
        page=page,
        page_size=page_size,
    )
    return paged_response(
        [AssessmentTemplateItemRead.model_validate(item) for item in items],
        total,
        page,
        page_size,
        "测评记录模板项列表获取成功",
    )


@router.get("/{workbook_id}", response_model=ApiResponse)
def get_assessment_template_workbook(workbook_id: str, db: Session = Depends(get_db)):
    workbook = service.get_workbook(db, workbook_id)
    return success_response(AssessmentTemplateWorkbookDetailRead.model_validate(workbook), "测评记录模板工作簿详情获取成功")


@router.patch("/{workbook_id}", response_model=ApiResponse)
def update_assessment_template_workbook(
    workbook_id: str,
    payload: AssessmentTemplateWorkbookUpdate,
    db: Session = Depends(get_db),
):
    workbook = service.update_workbook(db, workbook_id, **payload.model_dump())
    return success_response(AssessmentTemplateWorkbookRead.model_validate(workbook), "测评记录模板工作簿更新成功")


@router.delete("/{workbook_id}", response_model=ApiResponse)
def delete_assessment_template_workbook(
    workbook_id: str,
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    result = service.delete_workbook(db, workbook_id, force=force)
    return success_response(result, "测评记录模板工作簿删除成功")


@router.get("/{workbook_id}/sheets", response_model=ApiResponse)
def list_assessment_template_sheets(
    workbook_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    sheets, total = service.list_sheets_page(db, workbook_id, page=page, page_size=page_size)
    return paged_response(
        [AssessmentTemplateSheetRead.model_validate(item) for item in sheets],
        total,
        page,
        page_size,
        "测评记录模板工作表列表获取成功",
    )
