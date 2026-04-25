from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse, list_response, success_response
from app.schemas.history_record import (
    HistoricalAssessmentImportRead,
    HistoricalAssessmentRecordRead,
    HistoricalAssessmentSimilarRead,
    HistoricalAssessmentSimilarSearchRequest,
)
from app.services.history_excel_import_service import HistoryExcelImportService
from app.services.history_record_search_service import HistoryRecordSearchService

router = APIRouter(prefix="/history-records", tags=["history-records"])
import_service = HistoryExcelImportService()
search_service = HistoryRecordSearchService()


@router.post("/import-excel", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def import_history_records_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    result = import_service.import_excel(db, file.filename or "history.xlsx", content)
    return success_response(HistoricalAssessmentImportRead.model_validate(result), "历史测评记录导入成功")


@router.get("", response_model=ApiResponse)
def list_history_records(
    asset_name: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    sheet_name: str | None = Query(default=None),
    control_point: str | None = Query(default=None),
    item_text: str | None = Query(default=None),
    compliance_result: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    records = search_service.list_records(
        db,
        asset_name=asset_name,
        asset_type=asset_type,
        sheet_name=sheet_name,
        control_point=control_point,
        item_text=item_text,
        compliance_result=compliance_result,
        keyword=keyword,
    )
    return list_response([HistoricalAssessmentRecordRead.model_validate(item) for item in records], "历史测评记录列表获取成功")


@router.get("/{record_id}", response_model=ApiResponse)
def get_history_record(record_id: str, db: Session = Depends(get_db)):
    record = search_service.get_record(db, record_id)
    return success_response(HistoricalAssessmentRecordRead.model_validate(record), "历史测评记录详情获取成功")


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
