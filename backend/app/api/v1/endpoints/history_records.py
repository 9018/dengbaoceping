from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse, list_response, paged_response, success_response
from app.schemas.history_record import (
    HistoricalAssessmentImportRead,
    HistoricalAssessmentRecordRead,
    HistoricalAssessmentSimilarRead,
    HistoricalAssessmentSimilarSearchRequest,
    HistoryRecordUpdate,
)
from app.services.history_excel_import_service import HistoryExcelImportService
from app.services.history_record_search_service import HistoryRecordSearchService

router = APIRouter(prefix="/history-records", tags=["history-records"])
import_service = HistoryExcelImportService()
search_service = HistoryRecordSearchService()


@router.post("/import-excel", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def import_history_records_excel(
    file: UploadFile = File(...),
    duplicate_policy: str = Query(default="skip"),
    db: Session = Depends(get_db),
):
    content = await file.read()
    result = import_service.import_excel(db, file.filename or "history.xlsx", content, duplicate_policy=duplicate_policy)
    return success_response(HistoricalAssessmentImportRead.model_validate(result), "历史测评记录导入成功")


@router.delete("/by-source", response_model=ApiResponse)
def delete_history_records_by_source(
    source_file: str | None = Query(default=None),
    source_file_hash: str | None = Query(default=None),
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    result = search_service.delete_by_source(
        db,
        source_file=source_file,
        source_file_hash=source_file_hash,
        force=force,
    )
    return success_response(result, "历史测评记录按来源删除成功")


@router.get("", response_model=ApiResponse)
def list_history_records(
    asset_name: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    sheet_name: str | None = Query(default=None),
    control_point: str | None = Query(default=None),
    item_text: str | None = Query(default=None),
    compliance_result: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    records, total = search_service.list_records_page(
        db,
        page=page,
        page_size=page_size,
        asset_name=asset_name,
        asset_type=asset_type,
        sheet_name=sheet_name,
        control_point=control_point,
        item_text=item_text,
        compliance_result=compliance_result,
        keyword=keyword,
    )
    return paged_response(
        [HistoricalAssessmentRecordRead.model_validate(item) for item in records],
        total,
        page,
        page_size,
        "历史测评记录列表获取成功",
    )


@router.get("/{record_id}", response_model=ApiResponse)
def get_history_record(record_id: str, db: Session = Depends(get_db)):
    record = search_service.get_record(db, record_id)
    return success_response(HistoricalAssessmentRecordRead.model_validate(record), "历史测评记录详情获取成功")


@router.patch("/{record_id}", response_model=ApiResponse)
def update_history_record(
    record_id: str,
    payload: HistoryRecordUpdate,
    db: Session = Depends(get_db),
):
    record = search_service.update_record(db, record_id, **payload.model_dump())
    return success_response(HistoricalAssessmentRecordRead.model_validate(record), "历史测评记录更新成功")


@router.delete("/{record_id}", response_model=ApiResponse)
def delete_history_record(
    record_id: str,
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    result = search_service.delete_record(db, record_id, force=force)
    return success_response(result, "历史测评记录删除成功")


@router.post("/search-similar", response_model=ApiResponse)
def search_similar_history_records(payload: HistoricalAssessmentSimilarSearchRequest, db: Session = Depends(get_db)):
    result = search_service.search_similar(
        db,
        ocr_text=payload.ocr_text,
        asset_type=payload.asset_type,
        page_type=payload.page_type,
        control_point=payload.control_point,
        item_text=payload.item_text,
    )
    return list_response([HistoricalAssessmentSimilarRead.model_validate(item) for item in result], "相似历史测评记录获取成功")
