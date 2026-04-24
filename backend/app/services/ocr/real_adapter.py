from __future__ import annotations

from app.core.exceptions import BadRequestException


class RealOCRAdapter:
    def run(self, *, evidence_id: str, filename: str, file_path: str, sample_id: str | None = None) -> dict:
        raise BadRequestException(
            "REAL_OCR_NOT_CONFIGURED",
            "真实OCR提供方尚未配置，请先完成provider接入",
            {"evidence_id": evidence_id, "filename": filename, "file_path": file_path, "sample_id": sample_id},
        )
