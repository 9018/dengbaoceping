from pathlib import Path
from io import BytesIO

import pytest
from openpyxl import Workbook

from app.core.config import settings
from app.models.evaluation_record import EvaluationRecord
from app.services.ocr.mock_adapter import MOCK_OCR_SAMPLES
from app.services.ocr.paddle_adapter import PaddleOCRAdapter
from tests.assessment_template_excel_utils import build_assessment_template_match_excel


@pytest.fixture(autouse=True)
def restore_ocr_provider():
    previous_provider = settings.OCR_PROVIDER
    settings.OCR_PROVIDER = "mock"
    PaddleOCRAdapter.reset_engine()
    yield
    settings.OCR_PROVIDER = previous_provider
    PaddleOCRAdapter.reset_engine()


def create_project(client):
    resp = client.post(
        "/api/v1/projects",
        json={"code": "PJT-EVD", "name": "证据项目", "project_type": "等级保护测评", "status": "draft"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def create_asset(
    client,
    project_id: str,
    *,
    filename: str,
    category: str = "device",
    category_label: str = "设备资产",
    primary_ip: str | None = None,
) -> str:
    resp = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "category": category,
            "category_label": category_label,
            "filename": filename,
            "primary_ip": primary_ip,
            "relative_path": f"assets/{filename}.txt",
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def upload_evidence(client, project_id: str, filename: str = "firewall_basic.txt") -> str:
    upload_resp = client.post(
        f"/api/v1/projects/{project_id}/evidences/upload",
        files={"file": (filename, b"hello evidence", "text/plain")},
        data={
            "title": "配置截图",
            "evidence_type": "screenshot",
            "summary": "边界防护",
            "device": "FW-01",
            "tags_json": '["tag-a", "tag-b"]',
            "source_ref": "manual-upload",
        },
    )
    assert upload_resp.status_code == 201
    upload_body = upload_resp.json()
    assert upload_body["success"] is True
    return upload_body["data"]["id"]


def import_template_match_library(client):
    resp = client.post(
        "/api/v1/assessment-templates/import-excel",
        files={
            "file": (
                "结果记录参考模板20260426.xlsx",
                build_assessment_template_match_excel(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]


def test_evidence_upload_and_delete(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id)

    upload_dir = Path(settings.UPLOAD_DIR) / project_id
    assert upload_dir.exists()
    stored_files = list(upload_dir.iterdir())
    assert stored_files

    list_resp = client.get(f"/api/v1/projects/{project_id}/evidences")
    assert list_resp.status_code == 200
    list_body = list_resp.json()
    assert list_body["meta"]["total"] == 1
    assert list_body["data"][0]["title"] == "配置截图"

    get_resp = client.get(f"/api/v1/evidences/{evidence_id}")
    assert get_resp.status_code == 200
    evidence = get_resp.json()["data"]
    assert evidence["device"] == "FW-01"
    assert evidence["asset_id"] is not None

    delete_resp = client.delete(f"/api/v1/evidences/{evidence_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["message"] == "证据已删除"
    assert not upload_dir.exists() or not any(upload_dir.iterdir())

    missing_resp = client.get(f"/api/v1/evidences/{evidence_id}")
    assert missing_resp.status_code == 404
    assert missing_resp.json()["error"]["code"] == "EVIDENCE_NOT_FOUND"


def test_upload_same_file_twice_creates_two_evidences(client):
    project_id = create_project(client)

    first_id = upload_evidence(client, project_id, "same-file.txt")
    second_id = upload_evidence(client, project_id, "same-file.txt")

    assert first_id != second_id

    list_resp = client.get(f"/api/v1/projects/{project_id}/evidences")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["meta"]["total"] == 2
    assert [item["title"] for item in body["data"]] == ["配置截图", "配置截图"]


def test_upload_evidence_under_missing_project(client):
    resp = client.post(
        "/api/v1/projects/missing-project/evidences/upload",
        files={"file": ("evidence.txt", b"hello evidence", "text/plain")},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_run_ocr_and_extract_fields(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")

    ocr_resp = client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "firewall_basic"})
    assert ocr_resp.status_code == 200
    ocr_body = ocr_resp.json()
    assert ocr_body["message"] == "OCR执行成功"
    assert ocr_body["data"]["ocr_status"] == "completed"
    assert ocr_body["data"]["ocr_provider"] == "mock_ocr"
    assert ocr_body["data"]["ocr_error_message"] is None
    assert "设备名称" in ocr_body["data"]["text_content"]

    ocr_result_resp = client.get(f"/api/v1/evidences/{evidence_id}/ocr-result")
    assert ocr_result_resp.status_code == 200
    ocr_result = ocr_result_resp.json()["data"]
    assert ocr_result["sample_id"] == "firewall_basic"
    assert ocr_result["status"] == "completed"
    assert ocr_result["raw_status"] == "completed"
    assert ocr_result["lines"]
    assert ocr_result["full_text"] == "\n".join(item["text"] for item in ocr_result["lines"])
    assert set(ocr_result["lines"][0]) == {"text", "confidence", "bbox"}

    extract_resp = client.post(
        f"/api/v1/evidences/{evidence_id}/extract-fields",
        json={"template_code": "security_device_basic"},
    )
    assert extract_resp.status_code == 200
    extract_body = extract_resp.json()
    assert extract_body["message"] == "字段抽取完成"
    assert extract_body["meta"]["total"] == 4

    fields = {item["field_name"]: item for item in extract_body["data"]}
    assert fields["device_name"]["raw_value"] == "FW-O1"
    assert fields["device_name"]["corrected_value"] == "FW-01"
    assert fields["device_name"]["status"] == "corrected"
    assert fields["device_ip"]["corrected_value"] == "10.0.0.1"

    list_fields_resp = client.get(f"/api/v1/evidences/{evidence_id}/fields")
    assert list_fields_resp.status_code == 200
    list_fields_body = list_fields_resp.json()
    assert list_fields_body["meta"]["total"] == 4


def test_run_ocr_reuses_existing_result_without_force(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")

    first_resp = client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "firewall_basic"})
    assert first_resp.status_code == 200
    first_processed_at = first_resp.json()["data"]["ocr_processed_at"]

    second_resp = client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "missing-sample"})
    assert second_resp.status_code == 200
    second_body = second_resp.json()["data"]
    assert second_body["ocr_processed_at"] == first_processed_at
    assert second_body["ocr_status"] == "completed"
    assert second_body["ocr_provider"] == "mock_ocr"


def test_run_ocr_force_reruns_and_replaces_previous_result(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")

    first_resp = client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "firewall_basic"})
    assert first_resp.status_code == 200

    MOCK_OCR_SAMPLES["force_warning"] = {
        "provider": "mock_ocr",
        "status": "failed",
        "sample_id": "force_warning",
        "full_text": "补录文本仍可使用",
        "pages": [{"page": 1, "confidence": 0.8, "text": "补录文本仍可使用", "segments": []}],
        "error": {"code": "MOCK_WARNING", "message": "存在告警", "details": {"kind": "partial"}},
    }
    try:
        forced_resp = client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "force_warning", "force": True})
    finally:
        MOCK_OCR_SAMPLES.pop("force_warning", None)

    assert forced_resp.status_code == 200
    body = forced_resp.json()["data"]
    assert body["ocr_status"] == "completed_with_warning"
    assert body["ocr_error_message"] == "存在告警"
    assert body["text_content"] == "补录文本仍可使用"


def test_manual_ocr_result_marks_completed_and_provider_manual(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "manual-ocr.txt")

    resp = client.patch(
        f"/api/v1/evidences/{evidence_id}/ocr-result",
        json={"text_content": "第一行\n第二行"},
    )

    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["ocr_status"] == "completed"
    assert body["ocr_provider"] == "manual"
    assert body["ocr_error_message"] is None
    assert body["text_content"] == "第一行\n第二行"

    result_resp = client.get(f"/api/v1/evidences/{evidence_id}/ocr-result")
    assert result_resp.status_code == 200
    result = result_resp.json()["data"]
    assert result["provider"] == "manual"
    assert result["status"] == "completed"
    assert result["lines"] == [
        {"text": "第一行", "confidence": 1.0, "bbox": []},
        {"text": "第二行", "confidence": 1.0, "bbox": []},
    ]


def test_manual_ocr_result_rejects_empty_text(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "manual-empty.txt")

    resp = client.patch(
        f"/api/v1/evidences/{evidence_id}/ocr-result",
        json={"text_content": "   \n"},
    )

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "OCR_MANUAL_TEXT_EMPTY"
def test_match_asset_hits_asset_name(client):
    project_id = create_project(client)
    create_asset(client, project_id, filename="FW-01", category="firewall", category_label="防火墙")
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")

    client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "firewall_basic"})
    client.post(f"/api/v1/evidences/{evidence_id}/extract-fields", json={"template_code": "security_device_basic"})

    resp = client.post(f"/api/v1/evidences/{evidence_id}/match-asset", json={"force": True})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["matched_asset_id"] is not None
    assert body["asset_match_status"] == "suggested"
    assert body["matched_asset"]["filename"] == "FW-01"
    assert body["asset_match_reasons_json"]["need_create_asset"] is False
    assert "资产名称" in "".join(body["asset_match_reasons_json"]["summary"])


def test_match_asset_hits_ip(client):
    project_id = create_project(client)
    asset_id = create_asset(client, project_id, filename="核心防火墙", category="firewall", category_label="防火墙", primary_ip="10.0.0.1")
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")

    client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "firewall_basic"})
    client.post(f"/api/v1/evidences/{evidence_id}/extract-fields", json={"template_code": "security_device_basic"})

    resp = client.post(f"/api/v1/evidences/{evidence_id}/match-asset", json={"force": True})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["matched_asset_id"] == asset_id
    assert body["asset_match_reasons_json"]["signals"]["device_ip"] == "10.0.0.1"
    assert "IP" in "".join(body["asset_match_reasons_json"]["summary"])


def test_match_asset_suggests_switch_type_from_h3c_keyword(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "switch_h3c.txt")

    client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "switch_h3c"})

    resp = client.post(f"/api/v1/evidences/{evidence_id}/match-asset", json={"force": True})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["asset_match_status"] == "unmatched"
    assert body["asset_match_reasons_json"]["suggested_asset_type"] == "switch"
    assert body["asset_match_reasons_json"]["need_create_asset"] is True


def test_match_asset_suggests_firewall_type_from_keyword(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_keyword.txt")

    client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "firewall_basic"})

    resp = client.post(f"/api/v1/evidences/{evidence_id}/match-asset", json={"force": True})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["asset_match_reasons_json"]["suggested_asset_type"] == "firewall"


def test_match_asset_returns_need_create_when_no_candidate(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "server_unknown.txt")

    client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "server_linux"})

    resp = client.post(f"/api/v1/evidences/{evidence_id}/match-asset", json={"force": True})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["matched_asset_id"] is None
    assert body["asset_match_status"] == "unmatched"
    assert body["asset_match_reasons_json"]["need_create_asset"] is True
    assert body["asset_match_reasons_json"]["suggested_asset_name"]


def test_confirm_asset_binds_evidence_and_asset(client):
    project_id = create_project(client)
    asset_id = create_asset(client, project_id, filename="FW-01", category="firewall", category_label="防火墙", primary_ip="10.0.0.1")
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")

    client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "firewall_basic"})
    client.post(f"/api/v1/evidences/{evidence_id}/extract-fields", json={"template_code": "security_device_basic"})
    client.post(f"/api/v1/evidences/{evidence_id}/match-asset", json={"force": True})

    resp = client.post(f"/api/v1/evidences/{evidence_id}/confirm-asset", json={"asset_id": asset_id})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["matched_asset_id"] == asset_id
    assert body["asset_match_status"] == "confirmed"
    assert body["asset_match_reasons_json"]["confirmed_asset_id"] == asset_id
    assert body["matched_asset"]["filename"] == "FW-01"


def test_match_guidance_returns_candidate_and_history(client, tmp_path):
    from tests.test_guidance_api import import_network_guidance, import_sample_history

    guidance_resp = import_network_guidance(client, tmp_path)
    history_resp = import_sample_history(client)
    assert guidance_resp.status_code == 201
    assert history_resp.status_code == 201

    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")
    client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "firewall_basic"})
    client.post(f"/api/v1/evidences/{evidence_id}/extract-fields", json={"template_code": "security_device_basic"})
    client.post(f"/api/v1/evidences/{evidence_id}/match-asset", json={"force": True})

    resp = client.post(f"/api/v1/evidences/{evidence_id}/match-guidance", json={"force": True})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["matched_guidance_id"] is not None
    assert body["guidance_match_status"] == "suggested"
    assert body["matched_guidance"]["section_title"] == "边界防护"
    assert body["guidance_match_reasons_json"]["top_history"]
    assert body["guidance_match_reasons_json"]["history_count"] >= 1


def test_confirm_guidance_binds_evidence_and_item(client, tmp_path):
    from tests.test_guidance_api import import_network_guidance

    guidance_resp = import_network_guidance(client, tmp_path)
    assert guidance_resp.status_code == 201
    guidance_id = client.get("/api/v1/guidance/items", params={"keyword": "边界防护"}).json()["data"]["items"][0]["id"]

    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "firewall_basic.txt")
    client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "firewall_basic"})

    resp = client.post(f"/api/v1/evidences/{evidence_id}/confirm-guidance", json={"guidance_id": guidance_id})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["matched_guidance_id"] == guidance_id
    assert body["guidance_match_status"] == "confirmed"
    assert body["guidance_match_reasons_json"]["confirmed_guidance_id"] == guidance_id
    assert body["matched_guidance"]["section_title"] == "边界防护"


def test_extract_fields_without_ocr_returns_400(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id)

    resp = client.post(f"/api/v1/evidences/{evidence_id}/extract-fields", json={})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "OCR_TEXT_NOT_FOUND"


def test_run_ocr_with_invalid_sample_returns_400(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id)

    resp = client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={"sample_id": "missing-sample"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "MOCK_OCR_SAMPLE_NOT_FOUND"


def test_run_paddle_ocr_success_with_stubbed_engine(client, monkeypatch):
    settings.OCR_PROVIDER = "paddle"
    PaddleOCRAdapter.reset_engine()

    class FakeEngine:
        def predict(self, file_path, use_textline_orientation=True):
            return [
                {
                    "rec_texts": ["设备名称：FW-01", "管理IP：10.0.0.1"],
                    "rec_scores": [0.99, 0.97],
                    "dt_polys": [
                        [[0, 0], [10, 0], [10, 10], [0, 10]],
                        [[0, 12], [10, 12], [10, 22], [0, 22]],
                    ],
                }
            ]

    monkeypatch.setattr(PaddleOCRAdapter, "_create_engine", classmethod(lambda cls: FakeEngine()))

    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "real-image.png")

    resp = client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={})

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["ocr_status"] == "completed"
    assert body["data"]["ocr_provider"] == "paddle_ocr"
    assert body["data"]["ocr_error_message"] is None
    assert body["data"]["text_content"] == "设备名称：FW-01\n管理IP：10.0.0.1"

    result_resp = client.get(f"/api/v1/evidences/{evidence_id}/ocr-result")
    assert result_resp.status_code == 200
    result = result_resp.json()["data"]
    assert result["lines"][0]["bbox"] == [[0, 0], [10, 0], [10, 10], [0, 10]]
    assert result["full_text"] == "\n".join(item["text"] for item in result["lines"])
    assert result["error"] is None


def test_run_paddle_ocr_failure_returns_structured_result(client, monkeypatch):
    settings.OCR_PROVIDER = "paddle"
    PaddleOCRAdapter.reset_engine()

    class FakeEngine:
        def predict(self, file_path, use_textline_orientation=True):
            raise RuntimeError("engine boom")

    monkeypatch.setattr(PaddleOCRAdapter, "_create_engine", classmethod(lambda cls: FakeEngine()))

    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "broken-image.png")

    resp = client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={})

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["ocr_status"] == "failed"
    assert body["data"]["ocr_provider"] == "paddle_ocr"
    assert body["data"]["ocr_error_message"] == "PaddleOCR 执行失败"
    assert body["data"]["text_content"] == ""

    result_resp = client.get(f"/api/v1/evidences/{evidence_id}/ocr-result")
    assert result_resp.status_code == 200
    result = result_resp.json()["data"]
    assert result["status"] == "failed"
    assert result["error"]["code"] == "PADDLE_OCR_RUN_FAILED"
    assert result["lines"] == []


def test_run_paddle_ocr_normalizes_failed_with_text_to_completed_with_warning(client, monkeypatch):
    settings.OCR_PROVIDER = "paddle"
    PaddleOCRAdapter.reset_engine()

    class FakeEngine:
        def predict(self, file_path, use_textline_orientation=True):
            return {"full_text": "兜底文本"}

    monkeypatch.setattr(PaddleOCRAdapter, "_create_engine", classmethod(lambda cls: FakeEngine()))

    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "warning-image.png")

    resp = client.post(
        f"/api/v1/evidences/{evidence_id}/ocr",
        json={"force": True},
    )

    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["ocr_status"] == "completed_with_warning"
    assert body["ocr_provider"] == "paddle_ocr"
    assert body["ocr_error_message"] == "PaddleOCR 原始结果未能完整解析为结构化行，已降级保留文本摘要"
    assert body["text_content"] == "兜底文本"

    result_resp = client.get(f"/api/v1/evidences/{evidence_id}/ocr-result")
    result = result_resp.json()["data"]
    assert result["status"] == "completed_with_warning"
    assert result["raw_status"] == "failed"
    assert result["error"]["code"] == "PADDLE_OCR_LINES_NORMALIZED_EMPTY"
def test_classify_page_api_uses_ocr_text(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "password-policy.txt")

    resp = client.post(
        f"/api/v1/evidences/{evidence_id}/classify-page",
        json={"ocr_text": "密码策略 密码长度 复杂度 大写字母 小写字母 数字 特殊字符 有效期"},
    )

    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["page_type"] == "password_policy"
    assert body["confidence"] >= 0.7
    assert "密码策略" in body["matched_keywords"]
    assert body["reason"]


def test_match_template_item_api_acceptance_cases(client):
    import_template_match_library(client)
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "template-match.txt")

    cases = [
        {
            "ocr_text": "查看系统-管理员账号-密码安全策略 最小密码长度 密码复杂度 有效期",
            "asset_type": "firewall",
            "expected_sheet": "外联防火墙A",
            "expected_control_point": "身份鉴别",
            "expected_item_prefix": "a）",
        },
        {
            "ocr_text": "查看监控-日志页面 审计日志 操作日志 管理员操作记录",
            "asset_type": "firewall",
            "expected_sheet": "外联防火墙A",
            "expected_control_point": "安全审计",
            "expected_item_prefix": "a）",
        },
        {
            "ocr_text": "display password-control 登录失败 锁定阈值 最小密码长度 密码复杂度",
            "asset_type": "switch",
            "expected_sheet": "核心交换机",
            "expected_control_point": "身份鉴别",
            "expected_item_prefix": "b）",
        },
        {
            "ocr_text": "打开本地安全策略 secpol.msc 最小密码长度 密码复杂度 账户锁定阈值",
            "asset_type": "server",
            "expected_sheet": "Windows服务器",
            "expected_control_point": "身份鉴别",
            "expected_item_prefix": "a）",
        },
    ]

    for case in cases:
        resp = client.post(
            f"/api/v1/evidences/{evidence_id}/match-template-item",
            json={
                "ocr_text": case["ocr_text"],
                "asset_type": case["asset_type"],
            },
        )
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert body["matched_template_item"] is not None
        assert body["matched_template_item"]["sheet_name"] == case["expected_sheet"]
        assert body["matched_template_item"]["control_point"] == case["expected_control_point"]
        assert body["matched_template_item"]["item_text"].startswith(case["expected_item_prefix"])
        assert body["score"] >= 0.45
        assert body["confidence"] >= 0.45
        assert body["candidates"]
        assert body["reason"]


def test_match_template_item_api_requires_text_or_fields(client):
    import_template_match_library(client)
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "empty-template-match.txt")

    resp = client.post(f"/api/v1/evidences/{evidence_id}/match-template-item", json={})

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "EVIDENCE_TEMPLATE_MATCH_INPUT_NOT_FOUND"


def test_match_history_api_returns_suggestion(client, db_session):
    from tests.history_excel_utils import build_final_assessment_excel

    import_resp = client.post(
        "/api/history-records/import-excel",
        files={
            "file": (
                "final.xlsx",
                build_final_assessment_excel(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert import_resp.status_code == 201
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "access-control.txt")

    resp = client.post(
        f"/api/v1/evidences/{evidence_id}/match-history",
        json={
            "ocr_text": "安全策略 访问控制 源地址 目的地址 服务 动作 命中数 默认拒绝",
            "asset_type": "firewall",
        },
    )

    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["page_type"] == "access_control_policy"
    assert body["matched_history_records"]
    assert body["suggested_control_point"] == "边界访问控制"
    assert "访问控制" in body["suggested_record_text"] or "日志" in body["suggested_record_text"]
    assert body["suggested_compliance_result"] in {"符合", "部分符合"}
    assert body["confidence"] >= 0.3
    assert body["reason"]
    assert db_session.query(EvaluationRecord).count() == 0


def test_match_history_api_low_confidence_is_suggestion_only(client, db_session):
    from tests.history_excel_utils import build_final_assessment_excel

    import_resp = client.post(
        "/api/history-records/import-excel",
        files={"file": ("final.xlsx", build_final_assessment_excel(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert import_resp.status_code == 201
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "unknown.txt")

    resp = client.post(f"/api/v1/evidences/{evidence_id}/match-history", json={"ocr_text": "无关截图内容"})

    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["confidence"] < 0.7
    assert db_session.query(EvaluationRecord).count() == 0


def test_classify_page_api_missing_evidence_returns_404(client):
    resp = client.post("/api/v1/evidences/missing-evidence/classify-page", json={"ocr_text": "密码策略"})

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "EVIDENCE_NOT_FOUND"


def test_match_history_api_requires_text_or_fields(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id, "empty.txt")

    resp = client.post(f"/api/v1/evidences/{evidence_id}/match-history", json={})

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "EVIDENCE_HISTORY_MATCH_INPUT_NOT_FOUND"


@pytest.mark.skipif(settings.OCR_PROVIDER != "real", reason="仅在真实OCR provider配置下验证占位返回")
def test_run_real_ocr_without_provider_config_returns_400(client):
    project_id = create_project(client)
    evidence_id = upload_evidence(client, project_id)

    resp = client.post(f"/api/v1/evidences/{evidence_id}/ocr", json={})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "REAL_OCR_NOT_CONFIGURED"
