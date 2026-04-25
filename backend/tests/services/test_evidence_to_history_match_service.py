import pytest

from app.core.exceptions import BadRequestException
from app.models.evidence import Evidence
from app.models.evaluation_record import EvaluationRecord
from app.models.history_record import HistoryRecord
from app.models.project import Project
from app.services.evidence_to_history_match_service import EvidenceToHistoryMatchService


@pytest.fixture()
def project(db_session):
    item = Project(code="PJT-HM", name="历史匹配项目", project_type="等级保护测评", status="draft")
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


def add_evidence(db_session, project, text: str) -> Evidence:
    item = Evidence(
        project_id=project.id,
        evidence_type="screenshot",
        title="配置截图",
        text_content=text,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


def add_history_record(
    db_session,
    *,
    asset_name: str = "出口防火墙-A",
    asset_type: str = "firewall",
    control_point: str = "身份鉴别",
    item_text: str = "应对登录的用户进行身份标识和鉴别，身份鉴别信息具有复杂度要求并定期更换。",
    record_text: str = "经核查，系统已配置密码策略，密码长度不少于 8 位，包含大写字母、小写字母、数字、特殊字符并设置有效期。",
    compliance_result: str = "符合",
    row_index: int = 3,
) -> HistoryRecord:
    item = HistoryRecord(
        source_file="final.xlsx",
        project_name="历史项目",
        sheet_name=asset_name,
        asset_name=asset_name,
        asset_type=asset_type,
        asset_ip="143.8.51.2",
        asset_version="V8.0.26",
        standard_type="安全计算环境",
        extension_standard="安全计算环境",
        control_point=control_point,
        item_text=item_text,
        evaluation_item=item_text,
        record_text=record_text,
        raw_text=record_text,
        compliance_result=compliance_result,
        compliance_status=compliance_result,
        score_weight=1.0,
        score=1.0,
        item_code=f"A-{row_index}",
        item_no=f"A-{row_index}",
        row_index=row_index,
        keywords_json=[control_point, "身份鉴别", "密码策略", "复杂度", "有效期", "访问控制", "安全策略", "源地址", "目的地址", "默认拒绝"],
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


def test_match_password_policy_history_record(db_session, project):
    add_history_record(db_session)
    evidence = add_evidence(db_session, project, "密码策略 密码长度 复杂度 大写字母 小写字母 数字 特殊字符 有效期")

    result = EvidenceToHistoryMatchService().match(db_session, evidence.id, asset_type="firewall")

    assert result["page_type"] == "password_policy"
    assert result["confidence"] >= 0.7
    assert result["suggested_control_point"] == "身份鉴别"
    assert "复杂度" in result["suggested_item_text"]
    assert result["suggested_compliance_result"] == "符合"
    assert result["matched_history_records"][0]["asset_name"] == "出口防火墙-A"
    assert result["reason"]


def test_match_access_control_history_record(db_session, project):
    add_history_record(
        db_session,
        control_point="边界访问控制",
        item_text="应在网络边界根据访问控制策略限制非授权访问。",
        record_text="经现场核查，已配置安全策略，包含源地址、目的地址、服务、动作、命中数，默认拒绝策略已启用。",
        row_index=4,
    )
    evidence = add_evidence(db_session, project, "安全策略 源地址 目的地址 服务 动作 命中数 默认拒绝")

    result = EvidenceToHistoryMatchService().match(db_session, evidence.id, asset_type="firewall")

    assert result["page_type"] == "access_control_policy"
    assert result["confidence"] >= 0.7
    assert result["suggested_control_point"] == "边界访问控制"
    assert "访问控制" in result["suggested_item_text"]
    assert result["matched_history_records"][0]["score"] >= result["matched_history_records"][-1]["score"]


def test_same_asset_type_increases_score(db_session, project):
    add_history_record(db_session, asset_name="出口防火墙-A", asset_type="firewall", row_index=3)
    add_history_record(db_session, asset_name="核心交换机-A", asset_type="switch", row_index=4)
    evidence = add_evidence(db_session, project, "密码策略 复杂度 有效期")

    result = EvidenceToHistoryMatchService().match(db_session, evidence.id, asset_type="firewall")

    scores = {item["asset_type"]: item["score"] for item in result["matched_history_records"]}
    assert scores["firewall"] > scores["switch"]


def test_low_confidence_match_does_not_create_evaluation_record(db_session, project):
    add_history_record(db_session)
    evidence = add_evidence(db_session, project, "无关截图内容")

    result = EvidenceToHistoryMatchService().match(db_session, evidence.id)

    assert result["confidence"] < 0.7
    assert "仅作为人工参考" in result["reason"] or not result["matched_history_records"]
    assert db_session.query(EvaluationRecord).count() == 0


def test_match_requires_text_or_fields(db_session, project):
    evidence = add_evidence(db_session, project, "")

    with pytest.raises(BadRequestException) as exc_info:
        EvidenceToHistoryMatchService().match(db_session, evidence.id)

    assert exc_info.value.code == "EVIDENCE_HISTORY_MATCH_INPUT_NOT_FOUND"
