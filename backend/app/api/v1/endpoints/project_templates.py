from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse, success_response
from app.schemas.project import ProjectTemplateImportRead, ProjectTemplateSummaryRead
from app.services.project_template_service import ProjectTemplateService

router = APIRouter(tags=["project-templates"])
service = ProjectTemplateService()


@router.post("/projects/{project_id}/templates/import-reference", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def import_project_reference_template(project_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    result = service.import_excel(db, project_id, file.filename or "reference.xlsx", content)
    return success_response(ProjectTemplateImportRead.model_validate(result), "项目模板导入成功")


@router.get("/projects/{project_id}/templates/reference", response_model=ApiResponse)
def get_project_reference_template(project_id: str, db: Session = Depends(get_db)):
    result = service.get_active_template_summary(db, project_id)
    if result is None:
        return success_response(None, "项目模板未导入")
    return success_response(ProjectTemplateSummaryRead.model_validate(result), "项目模板获取成功")
