from app.core.exceptions import BadRequestException
from app.services.assessment_template_import_service import AssessmentTemplateImportService
from tests.assessment_template_excel_utils import build_assessment_template_excel, build_assessment_template_excel_without_header


def test_import_service_finds_header_and_inherits_values():
    service = AssessmentTemplateImportService()
    workbook = service._load_workbook("assessment.xlsx", build_assessment_template_excel())
    parsed_sheet = service._parse_sheet("外联防火墙A", workbook["外联防火墙A"].iter_rows(values_only=True))
    assert parsed_sheet is not None
    assert len(parsed_sheet.items) == 2
    assert parsed_sheet.items[0].standard_type == "安全通信网络"
    assert parsed_sheet.items[1].standard_type == "安全通信网络"
    assert parsed_sheet.items[1].control_point == "访问控制"
    assert parsed_sheet.items[0].raw_row_json["alternative_templates"] == ["样例A1", "样例A2", "样例A3"]


def test_import_service_rejects_missing_header(db_session):
    service = AssessmentTemplateImportService()
    try:
        service.import_excel(db_session, "broken.xlsx", build_assessment_template_excel_without_header())
        raise AssertionError("expected BadRequestException")
    except BadRequestException as exc:
        assert exc.code == "ASSESSMENT_TEMPLATE_HEADER_NOT_FOUND"


def test_import_service_rejects_non_xlsx(db_session):
    service = AssessmentTemplateImportService()
    try:
        service.import_excel(db_session, "broken.csv", b"not-excel")
        raise AssertionError("expected BadRequestException")
    except BadRequestException as exc:
        assert exc.code == "ASSESSMENT_TEMPLATE_INVALID_TYPE"
