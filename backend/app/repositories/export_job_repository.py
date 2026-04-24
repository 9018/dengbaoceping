from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.export_job import ExportJob


class ExportJobRepository:
    def create(self, db: Session, export_job: ExportJob) -> ExportJob:
        db.add(export_job)
        db.flush()
        return export_job

    def get(self, db: Session, export_id: str) -> ExportJob | None:
        return db.get(ExportJob, export_id)

    def list_by_project(self, db: Session, project_id: str) -> list[ExportJob]:
        return (
            db.query(ExportJob)
            .filter(ExportJob.project_id == project_id)
            .order_by(ExportJob.created_at.desc())
            .all()
        )
