from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def list(self, db: Session) -> list[Project]:
        return db.query(Project).order_by(Project.created_at.desc()).all()

    def get(self, db: Session, project_id: str) -> Project | None:
        return db.get(Project, project_id)

    def get_by_code(self, db: Session, code: str) -> Project | None:
        return db.query(Project).filter(Project.code == code).first()

    def create(self, db: Session, project: Project) -> Project:
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def update(self, db: Session, project: Project) -> Project:
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def delete(self, db: Session, project: Project) -> None:
        db.delete(project)
        db.commit()
