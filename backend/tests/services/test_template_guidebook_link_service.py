from pathlib import Path

from app.models.assessment_template import AssessmentTemplateItem, TemplateGuidebookLink
from app.services.assessment_template_import_service import AssessmentTemplateImportService
from app.services.guidance_service import GuidanceService
from app.services.template_guidebook_link_service import TemplateGuidebookLinkService
from tests.assessment_template_excel_utils import build_assessment_template_match_excel
from tests.test_guidance_api import configure_guidance_path, write_guidance_file


GUIDANCE_CONTENT = """
# 网络安全
## 身份鉴别
应核查管理员身份鉴别机制。
应查看密码安全策略、口令复杂度、最小密码长度和登录失败锁定阈值配置。
应提供密码策略截图或 display password-control、display password policy 命令输出。
记录建议：经现场核查，管理员账号已启用口令复杂度、最小密码长度和登录失败锁定策略。

## 安全审计
应核查管理员操作日志留存情况。
应查看审计日志、操作日志和管理员操作记录。
应提供日志页面截图或日志审计配置截图。
预期结果：应提供管理员操作日志留存记录。
""".strip()


def prepare_template_and_guidance(db_session, tmp_path: Path):
    guidance_path = write_guidance_file(tmp_path, GUIDANCE_CONTENT)
    configure_guidance_path(guidance_path)

    guidance_service = GuidanceService()
    guidance_service.import_markdown(db_session)

    import_service = AssessmentTemplateImportService()
    import_service.import_excel(db_session, "结果记录参考模板20260426.xlsx", build_assessment_template_match_excel())

    service = TemplateGuidebookLinkService()
    firewall_item = (
        db_session.query(AssessmentTemplateItem)
        .filter(AssessmentTemplateItem.sheet_name == "外联防火墙A", AssessmentTemplateItem.item_code == "A-01")
        .first()
    )
    return service, firewall_item


def test_link_guidebook_writes_ranked_links(db_session, tmp_path: Path):
    service, template_item = prepare_template_and_guidance(db_session, tmp_path)

    result = service.link_guidebook(db_session, template_item.id)

    assert result["template_item_id"] == template_item.id
    assert result["linked_count"] >= 1
    links = db_session.query(TemplateGuidebookLink).filter(TemplateGuidebookLink.template_item_id == template_item.id).all()
    assert len(links) == result["linked_count"]
    assert result["top_score"] == max(link.match_score for link in links)


def test_list_guidebook_links_returns_guidance_details(db_session, tmp_path: Path):
    service, template_item = prepare_template_and_guidance(db_session, tmp_path)
    service.link_guidebook(db_session, template_item.id)

    rows = service.list_guidebook_links(db_session, template_item.id)

    assert rows
    assert rows[0]["template_item_id"] == template_item.id
    assert rows[0]["guidance_item"].section_title == rows[0]["section_title"]
    assert "match_score" in rows[0]
    assert "match_reason" in rows[0]
    assert "check_points" in rows[0]
    assert "evidence_requirements" in rows[0]


def test_link_guidebook_replaces_old_results_without_duplicates(db_session, tmp_path: Path):
    service, template_item = prepare_template_and_guidance(db_session, tmp_path)

    first = service.link_guidebook(db_session, template_item.id)
    second = service.link_guidebook(db_session, template_item.id)

    links = db_session.query(TemplateGuidebookLink).filter(TemplateGuidebookLink.template_item_id == template_item.id).all()
    guidance_ids = [link.guidance_item_id for link in links]
    assert len(guidance_ids) == len(set(guidance_ids))
    assert second["linked_count"] == len(links)
    assert first["linked_count"] == second["linked_count"]
