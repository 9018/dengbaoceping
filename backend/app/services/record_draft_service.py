from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.repositories.evidence_fact_repository import EvidenceFactRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.project_assessment_table_repository import ProjectAssessmentTableRepository
from app.services.record_generation_service import RecordGenerationService
from app.services.template_guidebook_link_service import TemplateGuidebookLinkService
from app.services.template_history_link_service import TemplateHistoryLinkService


class RecordDraftService:
    def __init__(self) -> None:
        self.project_assessment_repository = ProjectAssessmentTableRepository()
        self.evidence_repository = EvidenceRepository()
        self.evidence_fact_repository = EvidenceFactRepository()
        self.record_generation_service = RecordGenerationService()
        self.template_guidebook_link_service = TemplateGuidebookLinkService()
        self.template_history_link_service = TemplateHistoryLinkService()

    def generate_draft(self, db: Session, project_assessment_item_id: str, evidence_id: str) -> dict[str, Any]:
        item = self.project_assessment_repository.get_item(db, project_assessment_item_id)
        if not item:
            raise NotFoundException("PROJECT_ASSESSMENT_ITEM_NOT_FOUND", "项目测评项不存在")
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence or evidence.project_id != item.project_id:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")

        facts = self.evidence_fact_repository.list_by_evidence(db, evidence_id)
        if not facts:
            raise BadRequestException("EVIDENCE_FACTS_NOT_FOUND", "请先识别页面类型和证据事实")

        source_template_item = item.source_template_item
        if not source_template_item:
            raise BadRequestException("PROJECT_ASSESSMENT_SOURCE_TEMPLATE_NOT_FOUND", "项目测评项缺少来源模板项")

        guidebook_links = self.template_guidebook_link_service.list_guidebook_links(db, source_template_item.id)
        if not guidebook_links:
            try:
                self.template_guidebook_link_service.link_guidebook(db, source_template_item.id)
            except BadRequestException:
                guidebook_links = []
            else:
                guidebook_links = self.template_guidebook_link_service.list_guidebook_links(db, source_template_item.id)

        history_links = self.template_history_link_service.list_history_links(db, source_template_item.id)
        if not history_links:
            try:
                self.template_history_link_service.link_history(db, source_template_item.id)
            except BadRequestException:
                history_links = []
            else:
                history_links = self.template_history_link_service.list_history_links(db, source_template_item.id)

        fact_map = self._build_fact_map(facts)
        page_type = fact_map.get("page_type") or facts[0].page_type or "unknown"
        matched_item = {
            "match_source": "assessment_template",
            "item_code": item.item_code,
            "item_no": item.item_code,
            "sheet_name": item.sheet_name,
            "row_index": item.row_index,
            "control_point": item.control_point,
            "level2": item.control_point,
            "item_text": item.item_text,
            "level3": item.item_text,
            "record_template": item.record_template,
            "default_compliance": item.default_compliance_result,
            "missing_fields": [],
        }
        generation_input = {
            "asset_name": evidence.device or getattr(evidence.asset, "filename", None) or evidence.title,
            "asset_type": getattr(evidence.asset, "category", None),
            "page_type": page_type,
            "matched_item": matched_item,
            "extracted_facts": fact_map,
            "similar_history_records": [self._serialize_history_link(row) for row in history_links],
        }
        generated = self.record_generation_service.generate(generation_input)
        guidance_refs = [self._serialize_guidance_link(row) for row in guidebook_links]
        history_refs = [self._serialize_history_link(row) for row in history_links]
        evidence_fact_refs = [self._serialize_fact(fact) for fact in facts]

        item.evidence_ids_json = [evidence.id]
        item.evidence_facts_json = evidence_fact_refs
        item.guidance_refs_json = guidance_refs
        item.history_refs_json = history_refs
        item.draft_record_text = generated["record_text"]
        item.draft_compliance_result = generated["compliance_result"]
        item.confidence = generated["confidence"]
        item.status = "drafted" if generated["confidence"] >= 0.7 else "pending_review"
        item.match_reason_json = {
            "reason": generated["evidence_summary"],
            "missing_evidence": generated["missing_evidence"],
            "page_type": page_type,
        }
        self.project_assessment_repository.update_item(db, item)

        for fact in facts:
            fact.project_assessment_item_id = item.id
            self.evidence_fact_repository.update(db, fact)

        return {
            "project_assessment_item_id": item.id,
            "draft_record_text": item.draft_record_text,
            "draft_compliance_result": item.draft_compliance_result,
            "confidence": item.confidence,
            "reason": generated["evidence_summary"],
            "missing_evidence": generated["missing_evidence"],
            "guidance_refs": guidance_refs,
            "history_refs": history_refs,
            "evidence_facts": evidence_fact_refs,
        }

    def _build_fact_map(self, facts) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for fact in facts:
            if fact.normalized_value not in (None, ""):
                result[fact.fact_key] = fact.normalized_value
            elif fact.value_number is not None:
                result[fact.fact_key] = fact.value_number
            elif fact.value_bool is not None:
                result[fact.fact_key] = fact.value_bool
            elif fact.value_json is not None:
                result[fact.fact_key] = fact.value_json
        return result

    def _serialize_guidance_link(self, row: dict) -> dict[str, Any]:
        return {
            "guidance_item_id": row.get("guidance_item_id"),
            "guidance_code": row.get("guidance_code"),
            "section_title": row.get("section_title"),
            "section_path": row.get("section_path"),
            "check_points": row.get("check_points") or [],
            "evidence_requirements": row.get("evidence_requirements") or [],
            "record_suggestion": row.get("record_suggestion"),
            "match_score": row.get("match_score"),
            "match_reason": row.get("match_reason") or {},
        }

    def _serialize_history_link(self, row: dict) -> dict[str, Any]:
        return {
            "id": row.get("history_record_id") or row.get("id"),
            "asset_name": row.get("asset_name"),
            "asset_type": row.get("asset_type"),
            "asset_ip": row.get("asset_ip"),
            "asset_version": row.get("asset_version"),
            "sheet_name": row.get("sheet_name"),
            "control_point": row.get("control_point"),
            "item_text": row.get("item_text"),
            "evaluation_item": row.get("evaluation_item"),
            "record_text": row.get("record_text"),
            "raw_text": row.get("raw_text"),
            "compliance_result": row.get("compliance_result"),
            "compliance_status": row.get("compliance_status"),
            "match_score": row.get("match_score"),
            "match_reason": row.get("match_reason") or {},
        }

    def _serialize_fact(self, fact) -> dict[str, Any]:
        return {
            "id": fact.id,
            "page_type": fact.page_type,
            "fact_group": fact.fact_group,
            "fact_key": fact.fact_key,
            "fact_name": fact.fact_name,
            "raw_value": fact.raw_value,
            "normalized_value": fact.normalized_value,
            "value_number": fact.value_number,
            "value_bool": fact.value_bool,
            "value_json": fact.value_json,
            "source_text": fact.source_text,
            "source_page": fact.source_page,
            "confidence": fact.confidence,
            "status": fact.status,
        }
