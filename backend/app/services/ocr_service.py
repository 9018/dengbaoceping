from __future__ import annotations

from datetime import UTC, datetime

from app.core.exceptions import BadRequestException, NotFoundException
from app.repositories.evidence_repository import EvidenceRepository
from app.services.ocr.factory import OCRAdapterFactory


class OCRService:
    TERMINAL_STATUSES = {"completed", "completed_with_warning", "failed"}

    def __init__(self) -> None:
        self.evidence_repository = EvidenceRepository()
        self.adapter_factory = OCRAdapterFactory()

    def run_ocr(self, db, evidence_id: str, sample_id: str | None = None, force: bool = False):
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")
        if not evidence.asset:
            raise BadRequestException("EVIDENCE_ASSET_NOT_FOUND", "证据未关联文件资产")
        if not force and evidence.ocr_result_json and evidence.ocr_status in self.TERMINAL_STATUSES:
            return evidence

        adapter = self.adapter_factory.create()
        result = adapter.run(
            evidence_id=evidence_id,
            filename=evidence.asset.filename,
            file_path=evidence.asset.absolute_path,
            sample_id=sample_id,
        )
        return self._persist_ocr_result(db, evidence, result)

    def save_manual_result(self, db, evidence_id: str, text_content: str):
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")

        normalized_text = text_content.strip()
        if not normalized_text:
            raise BadRequestException("OCR_MANUAL_TEXT_EMPTY", "手工录入 OCR 文本不能为空")

        result = {
            "provider": "manual",
            "status": "completed",
            "full_text": normalized_text,
            "lines": [
                {
                    "text": line,
                    "confidence": 1.0,
                    "bbox": [],
                }
                for line in normalized_text.splitlines()
                if line.strip()
            ],
            "processed_at": datetime.now(UTC).isoformat(),
            "evidence_id": evidence.id,
            "filename": evidence.asset.filename if evidence.asset else None,
            "file_path": evidence.asset.absolute_path if evidence.asset else None,
            "sample_id": None,
            "error": None,
        }
        return self._persist_ocr_result(db, evidence, result)

    def get_ocr_result(self, db, evidence_id: str):
        evidence = self.evidence_repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")
        if not evidence.ocr_result_json:
            raise NotFoundException("OCR_RESULT_NOT_FOUND", "OCR结果不存在")
        return evidence.ocr_result_json

    def _persist_ocr_result(self, db, evidence, result: dict):
        normalized_result = self._normalize_result(result)
        error = normalized_result.get("error") if isinstance(normalized_result.get("error"), dict) else None

        evidence.text_content = normalized_result.get("full_text") or ""
        evidence.ocr_result_json = normalized_result
        evidence.ocr_status = normalized_result.get("status")
        evidence.ocr_provider = normalized_result.get("provider")
        evidence.ocr_error_message = error.get("message") if error else None
        evidence.ocr_error_json = error
        processed_at = normalized_result.get("processed_at")
        evidence.ocr_processed_at = datetime.fromisoformat(processed_at) if processed_at else None
        return self.evidence_repository.update(db, evidence)

    def _normalize_result(self, result: dict) -> dict:
        normalized = dict(result)
        lines = normalized.get("lines") if isinstance(normalized.get("lines"), list) else []
        full_text = str(normalized.get("full_text") or "").strip()
        if not full_text and lines:
            full_text = "\n".join(str(line.get("text") or "").strip() for line in lines if isinstance(line, dict) and str(line.get("text") or "").strip())
        normalized["full_text"] = full_text

        raw_status = str(normalized.get("status") or "").strip() or None
        normalized_status = self._normalize_status(raw_status, full_text)
        normalized["raw_status"] = raw_status
        normalized["status"] = normalized_status
        normalized.setdefault("lines", lines)
        normalized.setdefault("error", None)
        return normalized

    def _normalize_status(self, raw_status: str | None, full_text: str) -> str:
        if raw_status in {"pending", "processing"}:
            return raw_status
        if full_text:
            return "completed" if raw_status == "completed" else "completed_with_warning"
        return "failed"
