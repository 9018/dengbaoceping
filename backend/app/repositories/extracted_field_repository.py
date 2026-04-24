from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.extracted_field import ExtractedField, ReviewAuditLog


class ExtractedFieldRepository:
    def list_by_evidence(self, db: Session, evidence_id: str) -> list[ExtractedField]:
        return (
            db.query(ExtractedField)
            .filter(ExtractedField.evidence_id == evidence_id)
            .order_by(ExtractedField.created_at.asc())
            .all()
        )

    def list_audit_logs(self, db: Session, field_id: str) -> list[ReviewAuditLog]:
        return (
            db.query(ReviewAuditLog)
            .filter(ReviewAuditLog.target_type == "field", ReviewAuditLog.target_id == field_id)
            .order_by(ReviewAuditLog.created_at.desc())
            .all()
        )

    def get(self, db: Session, field_id: str) -> ExtractedField | None:
        return db.get(ExtractedField, field_id)

    def delete_by_evidence(self, db: Session, evidence_id: str) -> None:
        db.query(ExtractedField).filter(ExtractedField.evidence_id == evidence_id).delete()
        db.commit()

    def bulk_create(self, db: Session, fields: list[ExtractedField]) -> list[ExtractedField]:
        db.add_all(fields)
        db.commit()
        for field in fields:
            db.refresh(field)
        return fields

    def update(self, db: Session, field: ExtractedField) -> ExtractedField:
        db.add(field)
        db.commit()
        db.refresh(field)
        return field

    def clear_record_by_evidence(self, db: Session, evidence_id: str) -> None:
        (
            db.query(ExtractedField)
            .filter(ExtractedField.evidence_id == evidence_id)
            .update({ExtractedField.record_id: None}, synchronize_session=False)
        )

    def attach_record(self, db: Session, record_id: str, field_ids: list[str]) -> None:
        if not field_ids:
            return
        (
            db.query(ExtractedField)
            .filter(ExtractedField.id.in_(field_ids))
            .update({ExtractedField.record_id: record_id}, synchronize_session=False)
        )

    def create_audit_log(self, db: Session, log: ReviewAuditLog) -> ReviewAuditLog:
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
