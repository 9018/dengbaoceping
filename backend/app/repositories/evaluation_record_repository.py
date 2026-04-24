from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from app.models.evaluation_record import EvaluationRecord, EvaluationRecordEvidence
from app.models.extracted_field import ReviewAuditLog


class EvaluationRecordRepository:
    def list_by_project(self, db: Session, project_id: str) -> list[EvaluationRecord]:
        return (
            db.query(EvaluationRecord)
            .options(
                selectinload(EvaluationRecord.evidence_links)
                .selectinload(EvaluationRecordEvidence.evidence),
            )
            .filter(EvaluationRecord.project_id == project_id)
            .order_by(EvaluationRecord.created_at.desc())
            .all()
        )

    def list_audit_logs(self, db: Session, record_id: str) -> list[ReviewAuditLog]:
        return (
            db.query(ReviewAuditLog)
            .filter(ReviewAuditLog.target_type == "record", ReviewAuditLog.target_id == record_id)
            .order_by(ReviewAuditLog.created_at.desc())
            .all()
        )

    def get(self, db: Session, record_id: str) -> EvaluationRecord | None:
        return db.get(EvaluationRecord, record_id)

    def get_by_project_and_evidence(self, db: Session, project_id: str, evidence_id: str) -> EvaluationRecord | None:
        return (
            db.query(EvaluationRecord)
            .join(EvaluationRecordEvidence, EvaluationRecordEvidence.evaluation_record_id == EvaluationRecord.id)
            .filter(EvaluationRecord.project_id == project_id, EvaluationRecordEvidence.evidence_id == evidence_id)
            .order_by(EvaluationRecord.created_at.desc())
            .first()
        )

    def create(self, db: Session, record: EvaluationRecord) -> EvaluationRecord:
        db.add(record)
        db.flush()
        return record

    def update(self, db: Session, record: EvaluationRecord) -> EvaluationRecord:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def add_evidence_link(
        self,
        db: Session,
        record_id: str,
        evidence_id: str,
        relation_type: str = "source",
    ) -> EvaluationRecordEvidence:
        link = EvaluationRecordEvidence(
            evaluation_record_id=record_id,
            evidence_id=evidence_id,
            relation_type=relation_type,
        )
        db.add(link)
        db.flush()
        return link

    def create_audit_log(self, db: Session, log: ReviewAuditLog) -> ReviewAuditLog:
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
