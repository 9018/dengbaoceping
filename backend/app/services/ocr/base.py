from __future__ import annotations

from typing import Any, Protocol, TypedDict


class OCRLine(TypedDict):
    text: str
    confidence: float | None
    bbox: list[Any]


class OCRError(TypedDict):
    code: str
    message: str
    details: Any


class OCRResult(TypedDict, total=False):
    provider: str
    status: str
    full_text: str
    lines: list[OCRLine]
    processed_at: str
    evidence_id: str
    filename: str
    file_path: str
    sample_id: str | None
    error: OCRError | None


class OCRAdapter(Protocol):
    def run(self, *, evidence_id: str, filename: str, file_path: str, sample_id: str | None = None) -> OCRResult:
        ...
