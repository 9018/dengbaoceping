from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse, MetaSchema, paged_response, success_response
from app.schemas.guidance import (
    GuidanceHistoryLinkRead,
    GuidanceHistoryLinkResult,
    GuidanceImportRead,
    GuidanceItemRead,
    GuidanceItemUpdate,
)
from app.services.guidance_history_link_service import GuidanceHistoryLinkService
from app.services.guidance_service import GuidanceService

router = APIRouter(prefix="/guidance", tags=["guidance"])
service = GuidanceService()
link_service = GuidanceHistoryLinkService()


@router.post("/import-md", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def import_guidance_markdown(db: Session = Depends(get_db)):
    result = service.import_markdown(db)
    return success_response(GuidanceImportRead.model_validate(result), "指导书导入成功")


@router.get("/items", response_model=ApiResponse)
def list_guidance_items(
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    result, total = service.list_items_page(db, keyword=keyword, page=page, page_size=page_size)
    items = [GuidanceItemRead.model_validate(item) for item in result["items"]]
    return ApiResponse(
        success=True,
        message="指导书列表获取成功",
        data={**result, "items": items, "total": total, "page": page, "page_size": page_size},
        meta=MetaSchema(total=total, page=page, page_size=page_size),
    )


@router.get("/items/{guidance_id}", response_model=ApiResponse)
def get_guidance_item(guidance_id: str, db: Session = Depends(get_db)):
    item = service.get_item(db, guidance_id)
    return success_response(GuidanceItemRead.model_validate(item), "指导书章节详情获取成功")


@router.patch("/items/{guidance_id}", response_model=ApiResponse)
def update_guidance_item(
    guidance_id: str,
    payload: GuidanceItemUpdate,
    db: Session = Depends(get_db),
):
    item = service.update_item(db, guidance_id, **payload.model_dump())
    return success_response(GuidanceItemRead.model_validate(item), "指导书章节更新成功")


@router.delete("/items/{guidance_id}", response_model=ApiResponse)
def delete_guidance_item(
    guidance_id: str,
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    result = service.delete_item(db, guidance_id, force=force)
    return success_response(result, "指导书章节删除成功")


@router.post("/{guidance_id}/link-history", response_model=ApiResponse)
def link_guidance_history(guidance_id: str, db: Session = Depends(get_db)):
    result = link_service.link_history(db, guidance_id)
    return success_response(GuidanceHistoryLinkResult.model_validate(result), "指导书关联历史记录成功")


@router.get("/{guidance_id}/history-records", response_model=ApiResponse)
def list_guidance_history_records(
    guidance_id: str,
    compliance_status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    result, total = link_service.list_history_by_guidance_page(
        db,
        guidance_id,
        compliance_status,
        page=page,
        page_size=page_size,
    )
    return paged_response(
        [GuidanceHistoryLinkRead.model_validate(item) for item in result],
        total,
        page,
        page_size,
        "指导书关联历史记录获取成功",
    )


@router.get("/search", response_model=ApiResponse)
def search_guidance_items(keyword: str = Query(...), db: Session = Depends(get_db)):
    items = service.search_items(db, keyword)
    return success_response([GuidanceItemRead.model_validate(item) for item in items], "指导书搜索成功")
