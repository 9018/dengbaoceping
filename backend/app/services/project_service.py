from app.core.exceptions import BadRequestException, NotFoundException
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self) -> None:
        self.repository = ProjectRepository()

    def list_projects(self, db):
        return self.repository.list(db)

    def get_project(self, db, project_id: str):
        project = self.repository.get(db, project_id)
        if not project:
            raise NotFoundException("PROJECT_NOT_FOUND", "项目不存在")
        return project

    def create_project(self, db, payload: ProjectCreate):
        if payload.code:
            existing = self.repository.get_by_code(db, payload.code)
            if existing:
                raise BadRequestException("PROJECT_CODE_EXISTS", "项目编码已存在")
        project = Project(**payload.model_dump())
        return self.repository.create(db, project)

    def update_project(self, db, project_id: str, payload: ProjectUpdate):
        project = self.get_project(db, project_id)
        if payload.code and payload.code != project.code:
            existing = self.repository.get_by_code(db, payload.code)
            if existing:
                raise BadRequestException("PROJECT_CODE_EXISTS", "项目编码已存在")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, key, value)
        return self.repository.update(db, project)

    def delete_project(self, db, project_id: str):
        project = self.get_project(db, project_id)
        self.repository.delete(db, project)
