from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse, list_response, success_response
from app.schemas.export import ExcelExportCreateRequest, ExportCreateRequest, ExportJobRead
from app.services.export_service import ExportService

router = APIRouter(tags=["exports"])
service = ExportService()


@router.post("/projects/{project_id}/export", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_project_export(project_id: str, payload: ExportCreateRequest, db: Session = Depends(get_db)):
    export_job = service.create_project_export(db, project_id, payload.format)
    return success_response(ExportJobRead.model_validate(export_job), "项目导出成功")


@router.post("/projects/{project_id}/export-excel", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_project_excel_export(project_id: str, payload: ExcelExportCreateRequest, db: Session = Depends(get_db)):
    export_job = service.create_project_excel_export(db, project_id, payload.mode)
    return success_response(ExportJobRead.model_validate(export_job), "Excel导出成功")


@router.get("/projects/{project_id}/export-jobs", response_model=ApiResponse)
def list_project_exports(project_id: str, db: Session = Depends(get_db)):
    export_jobs = [ExportJobRead.model_validate(item) for item in service.list_project_exports(db, project_id)]
    return list_response(export_jobs, "项目导出任务列表获取成功")


@router.get("/exports/{export_id}/download")
def download_export(export_id: str, db: Session = Depends(get_db)):
    return service.download_export(db, export_id)
