from app.models.assessment_template import AssessmentTemplateItem, TemplateHistoryLink
from app.services.assessment_template_import_service import AssessmentTemplateImportService
from app.services.history_import_service import HistoryImportService
from app.services.template_history_link_service import TemplateHistoryLinkService
from tests.assessment_template_excel_utils import build_assessment_template_match_excel
from tests.history_excel_utils import build_history_excel


def prepare_template_and_history(db_session):
    history_import = HistoryImportService()
    history_import.import_excel(db_session, "history.xlsx", build_history_excel())

    import_service = AssessmentTemplateImportService()
    import_service.import_excel(db_session, "结果记录参考模板20260426.xlsx", build_assessment_template_match_excel())

    service = TemplateHistoryLinkService()
    firewall_item = (
        db_session.query(AssessmentTemplateItem)
        .filter(AssessmentTemplateItem.sheet_name == "外联防火墙A", AssessmentTemplateItem.item_code == "A-01")
        .first()
    )
    return service, firewall_item



def test_link_history_writes_ranked_links(db_session):
    service, template_item = prepare_template_and_history(db_session)

    result = service.link_history(db_session, template_item.id)

    assert result["template_item_id"] == template_item.id
    assert result["linked_count"] >= 1
    links = db_session.query(TemplateHistoryLink).filter(TemplateHistoryLink.template_item_id == template_item.id).all()
    assert len(links) == result["linked_count"]
    assert result["top_score"] == max(link.match_score for link in links)



def test_list_history_links_returns_history_details(db_session):
    service, template_item = prepare_template_and_history(db_session)
    service.link_history(db_session, template_item.id)

    rows = service.list_history_links(db_session, template_item.id)

    assert rows
    assert rows[0]["template_item_id"] == template_item.id
    assert rows[0]["history_record"].sheet_name == rows[0]["sheet_name"]
    assert "match_score" in rows[0]
    assert "match_reason" in rows[0]
    assert "record_text" in rows[0]
    assert "compliance_result" in rows[0]



def test_list_history_links_supports_compliance_filter(db_session):
    service, template_item = prepare_template_and_history(db_session)
    service.link_history(db_session, template_item.id)

    rows = service.list_history_links(db_session, template_item.id, "符合")

    assert rows
    assert all((row["compliance_result"] or row["compliance_status"]) == "符合" for row in rows)



def test_link_history_replaces_old_results_without_duplicates(db_session):
    service, template_item = prepare_template_and_history(db_session)

    first = service.link_history(db_session, template_item.id)
    second = service.link_history(db_session, template_item.id)

    links = db_session.query(TemplateHistoryLink).filter(TemplateHistoryLink.template_item_id == template_item.id).all()
    history_ids = [link.history_record_id for link in links]
    assert len(history_ids) == len(set(history_ids))
    assert second["linked_count"] == len(links)
    assert first["linked_count"] == second["linked_count"]
