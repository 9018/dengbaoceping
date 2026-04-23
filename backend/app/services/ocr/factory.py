from __future__ import annotations

from app.services.ocr.mock_adapter import MockOCRAdapter


class OCRAdapterFactory:
    def create(self):
        return MockOCRAdapter()
