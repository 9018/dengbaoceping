from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse, list_response, success_response
from app.schemas.history_record import (
    HistoryGuidanceLinkRead,
    HistoryImportRead,
    HistoryPhraseSummaryRead,
    HistoryRecordRead,
    HistorySimilarRead,
    HistoryStatsRead,
)
from app.services.guidance_history_link_service import GuidanceHistoryLinkService
from app.services.history_import_service import HistoryImportService
from app.services.history_search_service import HistorySearchService

router = APIRouter(prefix="/history", tags=["history"])
import_service = HistoryImportService()
search_service = HistorySearchService()
link_service = GuidanceHistoryLinkService()


@router.post("/import-excel", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def import_history_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    result = import_service.import_excel(db, file.filename or "history.xlsx", content)
    return success_response(HistoryImportRead.model_validate(result), "历史测评记录导入成功")


@router.get("/records", response_model=ApiResponse)
def list_history_records(
    sheet_name: str | None = Query(default=None),
    control_point: str | None = Query(default=None),
    compliance_status: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    records = search_service.list_records(
        db,
        sheet_name=sheet_name,
        control_point=control_point,
        compliance_status=compliance_status,
        asset_type=asset_type,
    )
    return list_response([HistoryRecordRead.model_validate(item) for item in records], "历史测评记录列表获取成功")


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
