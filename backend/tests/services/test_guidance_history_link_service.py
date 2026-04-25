from pathlib import Path

from app.models.guidance_history_link import GuidanceHistoryLink
from app.services.guidance_history_link_service import GuidanceHistoryLinkService
from app.services.history_import_service import HistoryImportService
from tests.test_guidance_api import configure_guidance_path, write_guidance_file
from tests.history_excel_utils import build_history_excel


GUIDANCE_CONTENT = """
# 网络安全
## 边界防护
应核查出口防火墙访问控制策略。
应查看访问控制日志留存情况。
记录建议：经现场核查，防火墙已配置访问控制策略，并开启日志留存。
""".strip()


def prepare_guidance_and_history(db_session, tmp_path: Path):
    guidance_path = write_guidance_file(tmp_path, GUIDANCE_CONTENT)
    configure_guidance_path(guidance_path)

    service = GuidanceHistoryLinkService()
    service.guidance_service.import_markdown(db_session)

    history_import = HistoryImportService()
    history_import.import_excel(db_session, "history.xlsx", build_history_excel())

    guidance_item = service.guidance_service.list_items(db_session)["items"][0]
    return service, guidance_item


def test_link_history_writes_ranked_links(db_session, tmp_path: Path):
    service, guidance_item = prepare_guidance_and_history(db_session, tmp_path)

    result = service.link_history(db_session, guidance_item.id)

    assert result["guidance_item_id"] == guidance_item.id
    assert result["linked_count"] >= 1
    links = db_session.query(GuidanceHistoryLink).filter(GuidanceHistoryLink.guidance_item_id == guidance_item.id).all()
    assert len(links) == result["linked_count"]
    assert result["top_score"] == max(link.match_score for link in links)


def test_list_history_by_guidance_supports_status_filter(db_session, tmp_path: Path):
    service, guidance_item = prepare_guidance_and_history(db_session, tmp_path)
    service.link_history(db_session, guidance_item.id)

    rows = service.list_history_by_guidance(db_session, guidance_item.id, "符合")

    assert rows
    assert all(row["compliance_status"] == "符合" for row in rows)
    assert all("match_score" in row for row in rows)
    assert all("match_reason" in row for row in rows)


def test_list_guidance_by_history_returns_reverse_links(db_session, tmp_path: Path):
    service, guidance_item = prepare_guidance_and_history(db_session, tmp_path)
    service.link_history(db_session, guidance_item.id)
    history_row = service.list_history_by_guidance(db_session, guidance_item.id)[0]

    rows = service.list_guidance_by_history(db_session, history_row["history_record_id"])

    assert rows
    assert rows[0]["guidance_item_id"] == guidance_item.id
    assert rows[0]["section_title"] == guidance_item.section_title


def test_link_history_replaces_old_results_without_duplicates(db_session, tmp_path: Path):
    service, guidance_item = prepare_guidance_and_history(db_session, tmp_path)

    first = service.link_history(db_session, guidance_item.id)
    second = service.link_history(db_session, guidance_item.id)

    links = db_session.query(GuidanceHistoryLink).filter(GuidanceHistoryLink.guidance_item_id == guidance_item.id).all()
    history_ids = [link.history_record_id for link in links]
    assert len(history_ids) == len(set(history_ids))
    assert second["linked_count"] == len(links)
    assert first["linked_count"] == second["linked_count"]
