from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import BadRequestException
from app.services.ocr.mock_adapter import MockOCRAdapter
from app.services.ocr.real_adapter import RealOCRAdapter


class OCRAdapterFactory:
    def create(self):
        if settings.OCR_PROVIDER == "mock":
            return MockOCRAdapter()
        if settings.OCR_PROVIDER == "real":
            return RealOCRAdapter()
        raise BadRequestException("OCR_PROVIDER_NOT_SUPPORTED", "未支持的OCR provider配置", settings.OCR_PROVIDER)
