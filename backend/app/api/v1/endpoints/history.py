from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse, list_response, paged_response, success_response
from app.schemas.history_record import (
    HistoryDuplicateGroupRead,
    HistoryFieldValueRead,
    HistoryFieldValueRenameRequest,
    HistoryGuidanceLinkRead,
    HistoryImportRead,
    HistoryPhraseSummaryRead,
    HistoryRecordRead,
    HistorySimilarRead,
    HistoryStatsRead,
    HistorySummaryRead,
)
from app.services.guidance_history_link_service import GuidanceHistoryLinkService
from app.services.history_import_service import HistoryImportService
from app.services.history_search_service import HistorySearchService

router = APIRouter(prefix="/history", tags=["history"])
import_service = HistoryImportService()
search_service = HistorySearchService()
link_service = GuidanceHistoryLinkService()


@router.post("/import-excel", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def import_history_excel(
    file: UploadFile = File(...),
    duplicate_policy: str = Query(default="skip"),
    db: Session = Depends(get_db),
):
    content = await file.read()
    result = import_service.import_excel(db, file.filename or "history.xlsx", content, duplicate_policy=duplicate_policy)
    return success_response(HistoryImportRead.model_validate(result), "历史测评记录导入成功")


@router.get("/summary", response_model=ApiResponse)
def get_history_summary(db: Session = Depends(get_db)):
    result = search_service.summary(db)
    return success_response(HistorySummaryRead.model_validate(result), "历史测评记录汇总获取成功")


@router.get("/duplicates", response_model=ApiResponse)
def list_history_duplicates(
    asset_name: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    sheet_name: str | None = Query(default=None),
    control_point: str | None = Query(default=None),
    item_text: str | None = Query(default=None),
    compliance_result: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    result = search_service.list_duplicate_groups(
        db,
        asset_name=asset_name,
        asset_type=asset_type,
        sheet_name=sheet_name,
        control_point=control_point,
        item_text=item_text,
        compliance_result=compliance_result,
        keyword=keyword,
    )
    return list_response([HistoryDuplicateGroupRead.model_validate(item) for item in result], "历史重复记录获取成功")


@router.delete("/duplicates", response_model=ApiResponse)
def delete_history_duplicates(
    strategy: str = Query(default="keep_first"),
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    result = search_service.delete_duplicate_groups(db, strategy=strategy, force=force)
    return success_response(result, "历史重复记录删除成功")


@router.get("/field-values/{field_name}", response_model=ApiResponse)
def list_history_field_values(field_name: str, db: Session = Depends(get_db)):
    result = search_service.list_field_values(db, field_name)
    return list_response([HistoryFieldValueRead.model_validate(item) for item in result], "历史记录字段值获取成功")


@router.patch("/field-values/{field_name}", response_model=ApiResponse)
def rename_history_field_value(
    field_name: str,
    payload: HistoryFieldValueRenameRequest,
    db: Session = Depends(get_db),
):
    result = search_service.rename_field_value(db, field_name, payload.from_value, payload.to_value)
    return success_response(result, "历史记录字段值更新成功")


@router.delete("/field-values/{field_name}", response_model=ApiResponse)
def delete_history_by_field_value(
    field_name: str,
    value: str = Query(...),
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    result = search_service.delete_by_field_value(db, field_name, value, force=force)
    return success_response(result, "历史记录按字段值删除成功")


@router.get("/records", response_model=ApiResponse)
def list_history_records(
    sheet_name: str | None = Query(default=None),
    control_point: str | None = Query(default=None),
    compliance_status: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    records, total = search_service.list_records_page(
        db,
        page=page,
        page_size=page_size,
        sheet_name=sheet_name,
        control_point=control_point,
        compliance_status=compliance_status,
        asset_type=asset_type,
    )
    return paged_response(
        [HistoryRecordRead.model_validate(item) for item in records],
        total,
        page,
        page_size,
        "历史测评记录列表获取成功",
    )


@router.get("/records/{record_id}", response_model=ApiResponse)
def get_history_record(record_id: str, db: Session = Depends(get_db)):
    record = search_service.get_record(db, record_id)
    return success_response(HistoryRecordRead.model_validate(record), "历史测评记录详情获取成功")


@router.get("/{history_id}/guidance-items", response_model=ApiResponse)
def list_history_guidance_items(history_id: str, db: Session = Depends(get_db)):
    result = link_service.list_guidance_by_history(db, history_id)
    return list_response([HistoryGuidanceLinkRead.model_validate(item) for item in result], "历史记录关联指导书获取成功")


@router.get("/search", response_model=ApiResponse)
def search_history_records(keyword: str = Query(...), db: Session = Depends(get_db)):
    records = search_service.search(db, keyword)
    return list_response([HistoryRecordRead.model_validate(item) for item in records], "历史测评记录搜索成功")


@router.get("/stats", response_model=ApiResponse)
def get_history_stats(db: Session = Depends(get_db)):
    result = search_service.stats(db)
    return success_response(HistoryStatsRead.model_validate(result), "历史测评记录统计获取成功")


@router.get("/similar", response_model=ApiResponse)
def get_similar_history_records(
    control_point: str = Query(...),
    evaluation_item: str = Query(...),
    asset_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    result = search_service.similar(db, control_point, evaluation_item, asset_type)
    return list_response([HistorySimilarRead.model_validate(item) for item in result], "相似历史测评记录获取成功")


@router.get("/phrases", response_model=ApiResponse)
def get_history_phrases(db: Session = Depends(get_db)):
    result = search_service.phrases(db)
    return list_response([HistoryPhraseSummaryRead.model_validate(item) for item in result], "历史测评记录句式统计获取成功")
