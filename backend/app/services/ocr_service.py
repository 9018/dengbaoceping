from __future__ import annotations

from datetime import datetime

from app.core.exceptions import BadRequestException, NotFoundException
from app.repositories.evidence_repository import EvidenceRepository
from app.services.ocr.factory import OCRAdapterFactory


class OCRService:
    def __init__(self) -> None:
        self.evidence_repository = EvidenceRepository()
        self.adapter_factory = OCRAdapterFactory()

    def run_ocr(self, db, evidence_id: str, sample_id: str | None = None):
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")
        if not evidence.asset:
            raise BadRequestException("EVIDENCE_ASSET_NOT_FOUND", "证据未关联文件资产")

        adapter = self.adapter_factory.create()
        result = adapter.run(
            evidence_id=evidence_id,
            filename=evidence.asset.filename,
            file_path=evidence.asset.absolute_path,
            sample_id=sample_id,
        )
        evidence.text_content = result.get("full_text")
        evidence.ocr_result_json = result
        evidence.ocr_status = result.get("status")
        evidence.ocr_provider = result.get("provider")
        processed_at = result.get("processed_at")
        evidence.ocr_processed_at = datetime.fromisoformat(processed_at) if processed_at else None
        return self.evidence_repository.update(db, evidence)

    def get_ocr_result(self, db, evidence_id: str):
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")
        if not evidence.ocr_result_json:
            raise NotFoundException("OCR_RESULT_NOT_FOUND", "OCR结果不存在")
        return evidence.ocr_result_json
