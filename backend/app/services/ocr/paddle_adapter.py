from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.config import settings
from app.core.exceptions import StorageException
from app.services.ocr.base import OCRError, OCRLine, OCRResult


class PaddleOCRAdapter:
    _engine: Any = None
    _engine_lock = Lock()

    @classmethod
    def reset_engine(cls) -> None:
        with cls._engine_lock:
            cls._engine = None

    @classmethod
    def _create_engine(cls):
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise StorageException(
                "PADDLE_OCR_DEPENDENCY_MISSING",
                "PaddleOCR 依赖未安装，请先安装 paddleocr 与 paddlepaddle",
                {"error": str(exc)},
            ) from exc

        try:
            return PaddleOCR(
                lang=settings.PADDLE_OCR_LANG,
                use_angle_cls=settings.PADDLE_OCR_USE_ANGLE_CLS,
                use_gpu=settings.PADDLE_OCR_USE_GPU,
            )
        except Exception as exc:
            raise StorageException(
                "PADDLE_OCR_INIT_FAILED",
                "PaddleOCR 初始化失败",
                {"error": str(exc)},
            ) from exc

    @classmethod
    def _get_engine(cls):
        if cls._engine is not None:
            return cls._engine

        with cls._engine_lock:
            if cls._engine is None:
                cls._engine = cls._create_engine()
        return cls._engine

    def run(self, *, evidence_id: str, filename: str, file_path: str, sample_id: str | None = None) -> OCRResult:
        path = Path(file_path)
        if not path.exists():
            return self._failed_result(
                evidence_id=evidence_id,
                filename=filename,
                file_path=file_path,
                sample_id=sample_id,
                code="PADDLE_OCR_FILE_NOT_FOUND",
                message="OCR 文件不存在",
                details={"file_path": file_path},
            )

        engine = self._get_engine()
        try:
            raw_result = engine.ocr(str(path), cls=settings.PADDLE_OCR_USE_ANGLE_CLS)
        except Exception as exc:
            return self._failed_result(
                evidence_id=evidence_id,
                filename=filename,
                file_path=file_path,
                sample_id=sample_id,
                code="PADDLE_OCR_RUN_FAILED",
                message="PaddleOCR 执行失败",
                details={"error": str(exc) or exc.__class__.__name__},
            )

        lines = self._normalize_lines(raw_result)
        if not lines:
            return self._failed_result(
                evidence_id=evidence_id,
                filename=filename,
                file_path=file_path,
                sample_id=sample_id,
                code="PADDLE_OCR_EMPTY_RESULT",
                message="PaddleOCR 未识别到文本",
                details={"filename": filename},
            )

        return {
            **self._base_result(
                evidence_id=evidence_id,
                filename=filename,
                file_path=file_path,
                sample_id=sample_id,
            ),
            "status": "completed",
            "full_text": "\n".join(line["text"] for line in lines if line["text"]),
            "lines": lines,
            "error": None,
        }

    def _base_result(self, *, evidence_id: str, filename: str, file_path: str, sample_id: str | None) -> OCRResult:
        return {
            "provider": "paddle_ocr",
            "processed_at": datetime.now(UTC).isoformat(),
            "evidence_id": evidence_id,
            "filename": filename,
            "file_path": file_path,
            "sample_id": sample_id,
        }

    def _failed_result(
        self,
        *,
        evidence_id: str,
        filename: str,
        file_path: str,
        sample_id: str | None,
        code: str,
        message: str,
        details: Any,
    ) -> OCRResult:
        error: OCRError = {
            "code": code,
            "message": message,
            "details": details,
        }
        return {
            **self._base_result(
                evidence_id=evidence_id,
                filename=filename,
                file_path=file_path,
                sample_id=sample_id,
            ),
            "status": "failed",
            "full_text": "",
            "lines": [],
            "error": error,
        }

    def _normalize_lines(self, raw_result: Any) -> list[OCRLine]:
        lines: list[OCRLine] = []
        if isinstance(raw_result, list):
            for page_result in raw_result:
                lines.extend(self._normalize_page(page_result))
        elif isinstance(raw_result, dict):
            lines.extend(self._normalize_page(raw_result))
        return [line for line in lines if line["text"]]

    def _normalize_page(self, page_result: Any) -> list[OCRLine]:
        if isinstance(page_result, dict):
            nested = page_result.get("res")
            if isinstance(nested, list):
                return self._normalize_page(nested)

            texts = page_result.get("rec_texts") or page_result.get("texts") or []
            scores = page_result.get("rec_scores") or page_result.get("scores") or []
            polygons = page_result.get("dt_polys") or page_result.get("polys") or []
            normalized: list[OCRLine] = []
            for index, text in enumerate(texts):
                normalized.append(
                    {
                        "text": str(text).strip(),
                        "confidence": self._normalize_confidence(scores[index] if index < len(scores) else None),
                        "bbox": self._normalize_bbox(polygons[index] if index < len(polygons) else None),
                    }
                )
            return normalized

        if not isinstance(page_result, list):
            return []

        normalized = []
        for entry in page_result:
            line = self._normalize_entry(entry)
            if line:
                normalized.append(line)
        return normalized

    def _normalize_entry(self, entry: Any) -> OCRLine | None:
        if isinstance(entry, dict):
            text = str(entry.get("text") or "").strip()
            if not text:
                return None
            return {
                "text": text,
                "confidence": self._normalize_confidence(entry.get("confidence")),
                "bbox": self._normalize_bbox(entry.get("bbox")),
            }

        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            return None

        bbox = self._normalize_bbox(entry[0])
        payload = entry[1]
        if isinstance(payload, (list, tuple)):
            text = str(payload[0] if payload else "").strip()
            confidence = payload[1] if len(payload) > 1 else None
        else:
            text = str(payload).strip()
            confidence = None

        if not text:
            return None
        return {
            "text": text,
            "confidence": self._normalize_confidence(confidence),
            "bbox": bbox,
        }

    def _normalize_confidence(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _normalize_bbox(self, value: Any) -> list[Any]:
        if value is None:
            return []
        if hasattr(value, "tolist"):
            value = value.tolist()
        if isinstance(value, (list, tuple)):
            return [self._normalize_bbox(item) if isinstance(item, (list, tuple)) or hasattr(item, "tolist") else item for item in value]
        return [value]
