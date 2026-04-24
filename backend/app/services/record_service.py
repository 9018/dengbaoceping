from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.evaluation_record import EvaluationRecord
from app.models.extracted_field import ReviewAuditLog
from app.repositories.evaluation_record_repository import EvaluationRecordRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.extracted_field_repository import ExtractedFieldRepository
from app.repositories.project_repository import ProjectRepository
from app.services.matching_service import MatchingService
from app.services.template_service import TemplateService


ALLOWED_RECORD_STATUS = {"generated", "generated_low_confidence", "reviewed", "approved", "exported"}
RECORD_STATUS_TRANSITIONS = {
    "generated": {"generated", "reviewed"},
    "generated_low_confidence": {"generated_low_confidence", "reviewed"},
    "reviewed": {"reviewed", "approved"},
    "approved": {"approved", "exported"},
    "exported": {"exported"},
}


class RecordService:
    def __init__(self) -> None:
        self.project_repository = ProjectRepository()
        self.evidence_repository = EvidenceRepository()
        self.field_repository = ExtractedFieldRepository()
        self.record_repository = EvaluationRecordRepository()
        self.matching_service = MatchingService()
        self.template_service = TemplateService()

    def generate_record(
        self,
        db: Session,
        project_id: str,
        evidence_id: str,
        device_type_override: str | None = None,
        force_regenerate: bool = False,
        selected_item_code: str | None = None,
        selected_template_code: str | None = None,
    ) -> EvaluationRecord:
        self._ensure_project_exists(db, project_id)
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")
        if evidence.project_id != project_id:
            raise BadRequestException("EVIDENCE_PROJECT_MISMATCH", "证据不属于当前项目")

        fields = self.field_repository.list_by_evidence(db, evidence_id)
        if not fields:
            raise BadRequestException("EXTRACTED_FIELDS_NOT_FOUND", "请先执行字段抽取再生成测评记录")

        if not force_regenerate:
            existing = self.record_repository.get_by_project_and_evidence(db, project_id, evidence_id)
            if existing:
                return existing

        match_result = self.matching_service.match(fields, device_type_override)
        selected_match = self.matching_service.select_candidate(match_result, selected_item_code, selected_template_code)
        if not selected_match:
            raise BadRequestException("EVALUATION_ITEM_NOT_MATCHED", "未找到可匹配的测评条目")

        rendered = self.template_service.render(
            selected_match["template_code"],
            match_result["field_map"],
            selected_match["missing_fields"],
        )
        needs_review = bool(selected_match["missing_fields"])
        low_confidence = selected_match["score"] < selected_match["pass_score"]
        status = "reviewed" if needs_review else "generated"
        if low_confidence and not needs_review:
            status = "generated_low_confidence"
        elif low_confidence:
            status = "reviewed"

        review_comment = rendered["review_comment"]
        if low_confidence:
            review_comment = f"{review_comment} 匹配得分低于阈值: {selected_match['score']} < {selected_match['pass_score']}。".strip()
        if selected_item_code or selected_template_code:
            review_comment = f"{review_comment} 本次按人工选择候选项生成。".strip()

        if force_regenerate:
            existing = self.record_repository.get_by_project_and_evidence(db, project_id, evidence_id)
            if existing:
                db.delete(existing)
                db.flush()

        record = EvaluationRecord(
            project_id=project_id,
            asset_id=evidence.asset_id,
            title=rendered["title"],
            template_code=selected_match["template_code"],
            item_code=selected_match["item_code"],
            matched_fields_json=selected_match["matched_fields"],
            match_candidates_json=self._serialize_candidates(match_result.get("top_candidates") or []),
            match_reasons_json={
                **selected_match["reasons"],
                "selected": selected_match["reasons"],
                "best_match_item_code": match_result.get("best_match", {}).get("item_code") if match_result.get("best_match") else None,
                "selection_mode": self._resolve_selection_mode(selected_item_code, selected_template_code),
                "device_type": match_result.get("device_type"),
            },
            match_score=selected_match["score"],
            review_comment=review_comment,
            indicator_l2=selected_match.get("level2"),
            indicator_l3=selected_match.get("level3"),
            record_text=rendered["record_content"],
            final_content=rendered["record_content"],
            status=status,
            source_type="generated",
        )
        self.record_repository.create(db, record)
        self.record_repository.add_evidence_link(db, record.id, evidence_id, relation_type="source")
        self.field_repository.clear_record_by_evidence(db, evidence_id)
        self.field_repository.attach_record(db, record.id, selected_match["matched_field_ids"])
        db.commit()
        db.refresh(record)
        return record

    def list_project_records(self, db: Session, project_id: str) -> list[EvaluationRecord]:
        self._ensure_project_exists(db, project_id)
        return self.record_repository.list_by_project(db, project_id)

    def get_record(self, db: Session, record_id: str) -> EvaluationRecord:
        record = self.record_repository.get(db, record_id)
        if not record:
            raise NotFoundException("EVALUATION_RECORD_NOT_FOUND", "测评记录不存在")
        return record

    def list_record_audit_logs(self, db: Session, record_id: str) -> list[ReviewAuditLog]:
        self.get_record(db, record_id)
        return self.record_repository.list_audit_logs(db, record_id)

    def update_record(self, db: Session, record_id: str, payload: dict) -> EvaluationRecord:
        record = self.get_record(db, record_id)
        if payload.get("status") is not None:
            self._validate_status(payload["status"])
            self._validate_transition(record.status, payload["status"])
        changed_fields = self._collect_changes(record, payload, {"record_content": "record_text"})
        for key, value in payload.items():
            if value is None:
                continue
            target_key = "record_text" if key == "record_content" else key
            setattr(record, target_key, value)
        if payload.get("reviewed_by"):
            record.reviewed_at = datetime.now(UTC)
        updated = self.record_repository.update(db, record)
        self._create_audit_log(db, record.id, "record_update", changed_fields, record.review_comment, record.reviewed_by)
        return updated

    def review_record(self, db: Session, record_id: str, payload: dict) -> EvaluationRecord:
        record = self.get_record(db, record_id)
        self._validate_status(payload.get("status"))
        self._validate_transition(record.status, payload["status"])
        review_payload = {
            "status": payload.get("status"),
            "final_content": payload.get("final_content", record.final_content or record.record_text),
            "review_comment": payload.get("review_comment"),
            "reviewed_by": payload.get("reviewed_by"),
        }
        changed_fields = self._collect_changes(record, review_payload)
        for key, value in review_payload.items():
            if value is not None:
                setattr(record, key, value)
        record.reviewed_at = datetime.now(UTC)
        updated = self.record_repository.update(db, record)
        self._create_audit_log(db, record.id, "record_review", changed_fields, record.review_comment, record.reviewed_by)
        return updated

    def _ensure_project_exists(self, db: Session, project_id: str) -> None:
        if not self.project_repository.get(db, project_id):
            raise NotFoundException("PROJECT_NOT_FOUND", "项目不存在")

    def _validate_status(self, status: str | None) -> None:
        if status is None or status not in ALLOWED_RECORD_STATUS:
            raise BadRequestException("INVALID_RECORD_STATUS", "记录状态不合法", sorted(ALLOWED_RECORD_STATUS))

    def _validate_transition(self, current_status: str | None, next_status: str) -> None:
        normalized_current_status = current_status or "generated"
        allowed_next_statuses = RECORD_STATUS_TRANSITIONS.get(normalized_current_status)
        if not allowed_next_statuses or next_status not in allowed_next_statuses:
            raise BadRequestException(
                "INVALID_RECORD_STATUS_TRANSITION",
                "记录状态流转不合法",
                {"current_status": current_status, "next_status": next_status, "allowed_statuses": sorted(allowed_next_statuses or [])},
            )

    def _collect_changes(self, record: EvaluationRecord, payload: dict, aliases: dict[str, str] | None = None) -> list[dict]:
        changed_fields = []
        aliases = aliases or {}
        for key, value in payload.items():
            if value is None:
                continue
            target_key = aliases.get(key, key)
            old_value = getattr(record, target_key, None)
            if old_value != value:
                changed_fields.append({"field": key, "before": old_value, "after": value})
        return changed_fields

    def _create_audit_log(self, db, record_id: str, action: str, changed_fields: list[dict], review_comment: str | None, reviewed_by: str | None) -> None:
        self.record_repository.create_audit_log(
            db,
            ReviewAuditLog(
                target_type="record",
                target_id=record_id,
                action=action,
                changed_fields_json=changed_fields,
                review_comment=review_comment,
                reviewed_by=reviewed_by,
            ),
        )

    def _serialize_candidates(self, candidates: list[dict]) -> list[dict]:
        serialized = []
        for candidate in candidates:
            serialized.append(
                {
                    "item_code": candidate.get("item_code"),
                    "template_code": candidate.get("template_code"),
                    "score": candidate.get("score"),
                    "pass_score": candidate.get("pass_score"),
                    "missing_fields": candidate.get("missing_fields"),
                    "matched_fields": candidate.get("matched_fields"),
                    "reasons": candidate.get("reasons"),
                }
            )
        return serialized

    def _resolve_selection_mode(self, selected_item_code: str | None, selected_template_code: str | None) -> str:
        if selected_item_code:
            return "manual_item"
        if selected_template_code:
            return "manual_template"
        return "best_match"
