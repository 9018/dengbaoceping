from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse, success_response, list_response
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])
service = ProjectService()


@router.get("", response_model=ApiResponse)
def list_projects(db: Session = Depends(get_db)):
    return list_response(service.list_projects(db))


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    return success_response(service.create_project(db, payload), "项目创建成功")


@router.get("/{project_id}", response_model=ApiResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    return success_response(service.get_project(db, project_id))


@router.put("/{project_id}", response_model=ApiResponse)
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)):
    return success_response(service.update_project(db, project_id, payload), "项目更新成功")


@router.delete("/{project_id}", response_model=ApiResponse)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    service.delete_project(db, project_id)
    return success_response(message="项目已删除")
