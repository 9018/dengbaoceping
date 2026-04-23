from __future__ import annotations

from datetime import datetime

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.extracted_field import ReviewAuditLog
from app.repositories.extracted_field_repository import ExtractedFieldRepository


ALLOWED_FIELD_STATUS = {"extracted", "reviewed", "corrected", "rejected"}


class FieldReviewService:
    def __init__(self) -> None:
        self.repository = ExtractedFieldRepository()

    def get_field(self, db, field_id: str):
        field = self.repository.get(db, field_id)
        if not field:
            raise NotFoundException("EXTRACTED_FIELD_NOT_FOUND", "抽取字段不存在")
        return field

    def update_field(self, db, field_id: str, payload: dict):
        field = self.get_field(db, field_id)
        changed_fields = self._collect_changes(field, payload)
        if "status" in payload and payload["status"] is not None:
            self._validate_status(payload["status"])
        self._apply_changes(field, payload)
        if payload.get("reviewed_by"):
            field.reviewed_at = datetime.now().astimezone()
        updated = self.repository.update(db, field)
        self._create_audit_log(db, field.id, "field_update", changed_fields, field.review_comment, field.reviewed_by)
        return updated

    def review_field(self, db, field_id: str, payload: dict):
        field = self.get_field(db, field_id)
        self._validate_status(payload.get("status"))
        review_payload = {
            "status": payload.get("status"),
            "corrected_value": payload.get("corrected_value", field.corrected_value),
            "review_comment": payload.get("review_comment"),
            "reviewed_by": payload.get("reviewed_by"),
        }
        changed_fields = self._collect_changes(field, review_payload)
        self._apply_changes(field, review_payload)
        field.reviewed_at = datetime.now().astimezone()
        updated = self.repository.update(db, field)
        self._create_audit_log(db, field.id, "field_review", changed_fields, field.review_comment, field.reviewed_by)
        return updated

    def _validate_status(self, status: str | None) -> None:
        if status is None or status not in ALLOWED_FIELD_STATUS:
            raise BadRequestException("INVALID_FIELD_STATUS", "字段状态不合法", sorted(ALLOWED_FIELD_STATUS))

    def _apply_changes(self, field, payload: dict) -> None:
        for key, value in payload.items():
            if value is not None:
                setattr(field, key, value)

    def _collect_changes(self, field, payload: dict) -> list[dict]:
        changed_fields = []
        for key, value in payload.items():
            if value is None:
                continue
            old_value = getattr(field, key, None)
            if old_value != value:
                changed_fields.append({"field": key, "before": old_value, "after": value})
        return changed_fields

    def _create_audit_log(self, db, field_id: str, action: str, changed_fields: list[dict], review_comment: str | None, reviewed_by: str | None) -> None:
        self.repository.create_audit_log(
            db,
            ReviewAuditLog(
                target_type="field",
                target_id=field_id,
                action=action,
                changed_fields_json=changed_fields,
                review_comment=review_comment,
                reviewed_by=reviewed_by,
            ),
        )
