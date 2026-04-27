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
            kwargs = {
                "lang": settings.PADDLE_OCR_LANG,
                "use_textline_orientation": settings.PADDLE_OCR_USE_ANGLE_CLS,
            }
            if settings.PADDLE_OCR_USE_GPU:
                kwargs["device"] = "gpu"
            return PaddleOCR(**kwargs)
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
            raw_result = engine.predict(
                str(path),
                use_textline_orientation=settings.PADDLE_OCR_USE_ANGLE_CLS,
            )
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
        fallback_text = self._extract_fallback_text(raw_result) if not lines else ""
        full_text = "\n".join(line["text"] for line in lines if line["text"]) or fallback_text
        if not full_text:
            return self._failed_result(
                evidence_id=evidence_id,
                filename=filename,
                file_path=file_path,
                sample_id=sample_id,
                code="PADDLE_OCR_EMPTY_RESULT",
                message="PaddleOCR 未识别到文本",
                details={"filename": filename},
            )

        error = None
        if not lines and fallback_text:
            error = {
                "code": "PADDLE_OCR_LINES_NORMALIZED_EMPTY",
                "message": "PaddleOCR 原始结果未能完整解析为结构化行，已降级保留文本摘要",
                "details": {"raw_result_type": type(raw_result).__name__},
            }

        return {
            **self._base_result(
                evidence_id=evidence_id,
                filename=filename,
                file_path=file_path,
                sample_id=sample_id,
            ),
            "status": "completed" if not error else "failed",
            "full_text": full_text,
            "lines": lines,
            "error": error,
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
        pages = self._coerce_pages(raw_result)
        for page_result in pages:
            lines.extend(self._normalize_page(page_result))
        return [line for line in lines if line["text"]]

    def _coerce_pages(self, raw_result: Any) -> list[Any]:
        if raw_result is None:
            return []
        if isinstance(raw_result, list):
            return raw_result
        if isinstance(raw_result, dict):
            return [raw_result]
        if hasattr(raw_result, "to_dict"):
            return self._coerce_pages(raw_result.to_dict())
        if hasattr(raw_result, "json"):
            try:
                return self._coerce_pages(raw_result.json())
            except TypeError:
                pass
        if hasattr(raw_result, "__dict__"):
            data = {key: value for key, value in vars(raw_result).items() if not key.startswith("_")}
            if data:
                return [data]
        return [raw_result]

    def _normalize_page(self, page_result: Any) -> list[OCRLine]:
        page_result = self._coerce_page_payload(page_result)

        if hasattr(page_result, "get"):
            nested = page_result.get("res")
            if nested is not None:
                nested_lines = self._normalize_lines(nested)
                if nested_lines:
                    return nested_lines

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
            return [line for line in normalized if line["text"]]

        if not isinstance(page_result, list):
            return []

        normalized = []
        for entry in page_result:
            line = self._normalize_entry(entry)
            if line:
                normalized.append(line)
        return normalized

    def _coerce_page_payload(self, page_result: Any) -> Any:
        if isinstance(page_result, str):
            return page_result
        if hasattr(page_result, "to_dict"):
            try:
                page_result = page_result.to_dict()
            except TypeError:
                pass
        if hasattr(page_result, "json") and not hasattr(page_result, "get"):
            try:
                page_result = page_result.json()
            except TypeError:
                pass
        if hasattr(page_result, "get") or isinstance(page_result, (list, tuple, dict, str)):
            return page_result
        if hasattr(page_result, "__dict__"):
            public_data = {key: value for key, value in vars(page_result).items() if not key.startswith("_")}
            if public_data:
                return public_data
            private_data = {key.lstrip("_"): value for key, value in vars(page_result).items() if key.startswith("_")}
            if private_data:
                return private_data
        return page_result

    def _normalize_entry(self, entry: Any) -> OCRLine | None:
        entry = self._coerce_page_payload(entry)

        if isinstance(entry, dict):
            text = str(entry.get("text") or entry.get("rec_text") or "").strip()
            if not text:
                return None
            return {
                "text": text,
                "confidence": self._normalize_confidence(entry.get("confidence") or entry.get("score") or entry.get("rec_score")),
                "bbox": self._normalize_bbox(entry.get("bbox") or entry.get("dt_poly") or entry.get("poly")),
            }

        if isinstance(entry, str):
            text = entry.strip()
            if not text:
                return None
            return {
                "text": text,
                "confidence": None,
                "bbox": [],
            }

        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            return None

        bbox = self._normalize_bbox(entry[0])
        payload = self._coerce_page_payload(entry[1])
        if isinstance(payload, dict):
            text = str(payload.get("text") or payload.get("rec_text") or "").strip()
            confidence = payload.get("confidence") or payload.get("score") or payload.get("rec_score")
        elif isinstance(payload, (list, tuple)):
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

    def _extract_fallback_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            for key in ("text", "full_text", "rec_text", "label"):
                text = str(value.get(key) or "").strip()
                if text:
                    return text
            return ""
        if isinstance(value, (list, tuple)):
            texts = [self._extract_fallback_text(item) for item in value]
            return "\n".join(text for text in texts if text)
        if hasattr(value, "tolist"):
            return self._extract_fallback_text(value.tolist())
        if hasattr(value, "__dict__"):
            texts = [self._extract_fallback_text(item) for item in vars(value).values()]
            return "\n".join(text for text in texts if text)
        return ""

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
