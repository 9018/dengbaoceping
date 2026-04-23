from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.evidence import Evidence


class EvidenceRepository:
    def list(self, db: Session) -> list[Evidence]:
        return db.query(Evidence).order_by(Evidence.created_at.desc()).all()

    def list_by_project(self, db: Session, project_id: str) -> list[Evidence]:
        return db.query(Evidence).filter(Evidence.project_id == project_id).order_by(Evidence.created_at.desc()).all()

    def get(self, db: Session, evidence_id: str) -> Evidence | None:
        return db.get(Evidence, evidence_id)

    def create(self, db: Session, evidence: Evidence) -> Evidence:
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return evidence

    def update(self, db: Session, evidence: Evidence) -> Evidence:
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return evidence

    def delete(self, db: Session, evidence: Evidence) -> None:
        db.delete(evidence)
        db.commit()
