from pathlib import Path

import builtins

import pytest

from app.core.exceptions import StorageException
from app.services.ocr.paddle_adapter import PaddleOCRAdapter


class FakeArray:
    def __init__(self, value):
        self._value = value

    def tolist(self):
        return self._value


class FakePredictRecord:
    def __init__(self, texts, scores, polys):
        self._texts = texts
        self._scores = scores
        self._polys = polys

    def get(self, key, default=None):
        mapping = {
            "rec_texts": self._texts,
            "rec_scores": self._scores,
            "dt_polys": self._polys,
        }
        return mapping.get(key, default)


def test_paddle_adapter_normalizes_nested_result_and_derives_full_text(tmp_path):
    evidence_file = tmp_path / "sample.png"
    evidence_file.write_bytes(b"fake image")

    adapter = PaddleOCRAdapter()

    class FakeEngine:
        def predict(self, file_path, use_textline_orientation=True):
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


def test_paddle_adapter_normalizes_predict_record_shape(tmp_path):
    evidence_file = tmp_path / "sample.png"
    evidence_file.write_bytes(b"fake image")

    adapter = PaddleOCRAdapter()

    class FakeEngine:
        def predict(self, file_path, use_textline_orientation=True):
            return [
                FakePredictRecord(
                    texts=["设备名称：FW-01", "管理IP：10.0.0.1"],
                    scores=[0.99, 0.97],
                    polys=[
                        [[0, 0], [10, 0], [10, 10], [0, 10]],
                        [[0, 12], [10, 12], [10, 22], [0, 22]],
                    ],
                )
            ]

    original_get_engine = PaddleOCRAdapter._get_engine
    PaddleOCRAdapter._get_engine = classmethod(lambda cls: FakeEngine())
    try:
        result = adapter.run(
            evidence_id="e-1b",
            filename="sample.png",
            file_path=str(evidence_file),
        )
    finally:
        PaddleOCRAdapter._get_engine = original_get_engine

    assert result["status"] == "completed"
    assert result["full_text"] == "设备名称：FW-01\n管理IP：10.0.0.1"
    assert result["lines"][0]["bbox"] == [[0, 0], [10, 0], [10, 10], [0, 10]]


def test_paddle_adapter_returns_failed_payload_on_runtime_error(tmp_path):
    evidence_file = tmp_path / "sample.png"
    evidence_file.write_bytes(b"fake image")

    adapter = PaddleOCRAdapter()

    class FakeEngine:
        def predict(self, file_path, use_textline_orientation=True):
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


def test_paddle_adapter_returns_failed_payload_when_file_missing(tmp_path):
    adapter = PaddleOCRAdapter()

    result = adapter.run(
        evidence_id="e-3",
        filename="missing.png",
        file_path=str(tmp_path / "missing.png"),
    )

    assert result["status"] == "failed"
    assert result["error"]["code"] == "PADDLE_OCR_FILE_NOT_FOUND"


def test_paddle_adapter_caches_engine_instance(monkeypatch):
    PaddleOCRAdapter.reset_engine()
    create_count = {"value": 0}

    class FakeEngine:
        def predict(self, file_path, use_textline_orientation=True):
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


def test_paddle_adapter_raises_storage_exception_when_dependency_missing(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "paddleocr":
            raise ImportError("missing paddle")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(StorageException) as exc_info:
        PaddleOCRAdapter._create_engine()

    assert exc_info.value.code == "PADDLE_OCR_DEPENDENCY_MISSING"
