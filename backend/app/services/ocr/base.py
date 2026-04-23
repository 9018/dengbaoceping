from __future__ import annotations

from typing import Protocol


class OCRAdapter(Protocol):
    def run(self, *, evidence_id: str, filename: str, sample_id: str | None = None) -> dict:
        ...
