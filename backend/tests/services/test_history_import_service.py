from io import BytesIO

from openpyxl import Workbook

from app.services.history_import_service import HistoryImportService
from tests.history_excel_utils import build_history_excel


service = HistoryImportService()


def build_missing_header_excel() -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "错误表"
    worksheet.append(["错误列", "控制点", "测评项", "结果记录", "符合情况", "分值", "编号"])
    worksheet.append(["安全通信网络", "边界访问控制", "应限制非授权访问", "已配置", "符合", 1.0, "A-01"])
    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def test_import_excel_parses_multiple_sheets(db_session):
    result = service.import_excel(db_session, "history.xlsx", build_history_excel())

    assert result["sheet_count"] == 2
    assert result["imported_count"] == 4
    assert result["skipped_count"] == 0
    assert result["compliance_status_counts"] == {"符合": 1, "部分符合": 1, "不符合": 1, "不适用": 1}


def test_import_excel_keeps_previous_values_for_merged_cells(db_session):
    service.import_excel(db_session, "history.xlsx", build_history_excel())
    records = service.repository.list_records(db_session, sheet_name="出口防火墙")

    assert len(records) == 2
    assert records[1].extension_standard == "安全通信网络"
    assert records[1].control_point == "边界访问控制"


def test_import_excel_rejects_invalid_extension(db_session):
    try:
        service.import_excel(db_session, "history.xls", b"invalid")
    except Exception as exc:
        assert getattr(exc, "code", None) == "HISTORY_EXCEL_INVALID_TYPE"
    else:
        raise AssertionError("expected invalid file type error")


def test_import_excel_rejects_missing_header(db_session):
    try:
        service.import_excel(db_session, "history.xlsx", build_missing_header_excel())
    except Exception as exc:
        assert getattr(exc, "code", None) == "HISTORY_EXCEL_HEADER_NOT_FOUND"
    else:
        raise AssertionError("expected missing header error")
