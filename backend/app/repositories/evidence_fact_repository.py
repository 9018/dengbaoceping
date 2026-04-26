from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.evidence_fact import EvidenceFact


class EvidenceFactRepository:
    def list_by_evidence(self, db: Session, evidence_id: str) -> list[EvidenceFact]:
        return (
            db.query(EvidenceFact)
            .filter(EvidenceFact.evidence_id == evidence_id)
            .order_by(EvidenceFact.created_at.asc())
            .all()
        )

    def list_by_project_assessment_item(self, db: Session, item_id: str) -> list[EvidenceFact]:
        return (
            db.query(EvidenceFact)
            .filter(EvidenceFact.project_assessment_item_id == item_id)
            .order_by(EvidenceFact.created_at.asc())
            .all()
        )

    def get(self, db: Session, fact_id: str) -> EvidenceFact | None:
        return db.get(EvidenceFact, fact_id)

    def replace_for_evidence(self, db: Session, evidence_id: str, facts: list[EvidenceFact]) -> list[EvidenceFact]:
        db.query(EvidenceFact).filter(EvidenceFact.evidence_id == evidence_id).delete()
        if facts:
            db.add_all(facts)
        db.commit()
        for fact in facts:
            db.refresh(fact)
        return facts

    def update(self, db: Session, fact: EvidenceFact) -> EvidenceFact:
        db.add(fact)
        db.commit()
        db.refresh(fact)
        return fact
