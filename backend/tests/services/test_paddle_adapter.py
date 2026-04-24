from pathlib import Path

from app.services.ocr.paddle_adapter import PaddleOCRAdapter


class FakeArray:
    def __init__(self, value):
        self._value = value

    def tolist(self):
        return self._value


def test_paddle_adapter_normalizes_nested_result_and_derives_full_text(tmp_path):
    evidence_file = tmp_path / "sample.png"
    evidence_file.write_bytes(b"fake image")

    adapter = PaddleOCRAdapter()

    class FakeEngine:
        def ocr(self, file_path, cls=True):
            return [
                [
                    [FakeArray([[1, 2], [3, 4], [5, 6], [7, 8]]), ("第一行", 0.98)],
                    [FakeArray([[9, 10], [11, 12], [13, 14], [15, 16]]), ("第二行", 0.95)],
                ]
            ]

    original_get_engine = PaddleOCRAdapter._get_engine
    PaddleOCRAdapter._get_engine = classmethod(lambda cls: FakeEngine())
    try:
        result = adapter.run(
            evidence_id="e-1",
            filename="sample.png",
            file_path=str(evidence_file),
        )
    finally:
        PaddleOCRAdapter._get_engine = original_get_engine

    assert result["status"] == "completed"
    assert result["provider"] == "paddle_ocr"
    assert result["full_text"] == "第一行\n第二行"
    assert result["lines"] == [
        {"text": "第一行", "confidence": 0.98, "bbox": [[1, 2], [3, 4], [5, 6], [7, 8]]},
        {"text": "第二行", "confidence": 0.95, "bbox": [[9, 10], [11, 12], [13, 14], [15, 16]]},
    ]
    assert result["error"] is None


def test_paddle_adapter_returns_failed_payload_on_runtime_error(tmp_path):
    evidence_file = tmp_path / "sample.png"
    evidence_file.write_bytes(b"fake image")

    adapter = PaddleOCRAdapter()

    class FakeEngine:
        def ocr(self, file_path, cls=True):
            raise RuntimeError("ocr crashed")

    original_get_engine = PaddleOCRAdapter._get_engine
    PaddleOCRAdapter._get_engine = classmethod(lambda cls: FakeEngine())
    try:
        result = adapter.run(
            evidence_id="e-2",
            filename="sample.png",
            file_path=str(evidence_file),
        )
    finally:
        PaddleOCRAdapter._get_engine = original_get_engine

    assert result["status"] == "failed"
    assert result["provider"] == "paddle_ocr"
    assert result["full_text"] == ""
    assert result["lines"] == []
    assert result["error"]["code"] == "PADDLE_OCR_RUN_FAILED"


def test_paddle_adapter_caches_engine_instance(monkeypatch):
    PaddleOCRAdapter.reset_engine()
    create_count = {"value": 0}

    class FakeEngine:
        def ocr(self, file_path, cls=True):
            return []

    def fake_create_engine(cls):
        create_count["value"] += 1
        return FakeEngine()

    monkeypatch.setattr(PaddleOCRAdapter, "_create_engine", classmethod(fake_create_engine))

    first = PaddleOCRAdapter._get_engine()
    second = PaddleOCRAdapter._get_engine()

    assert first is second
    assert create_count["value"] == 1
    PaddleOCRAdapter.reset_engine()
