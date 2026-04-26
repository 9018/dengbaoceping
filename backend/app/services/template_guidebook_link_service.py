from __future__ import annotations

import re
from collections import Counter

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.assessment_template import AssessmentTemplateItem, TemplateGuidebookLink
from app.models.guidance_item import GuidanceItem
from app.repositories.template_guidebook_link_repository import TemplateGuidebookLinkRepository
from app.services.guidance_service import GuidanceService
from app.services.template_item_match_service import TemplateItemMatchService


class TemplateGuidebookLinkService:
    TOP_N = 5
    TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_./:-]{2,}|[一-鿿]{2,}")
    STOPWORDS = {
        "进行",
        "结果",
        "记录",
        "情况",
        "控制点",
        "测评项",
        "扩展标准",
        "符合",
        "部分符合",
        "不符合",
        "不适用",
        "核查",
        "现场",
        "查看",
        "检查",
        "确认",
        "当前",
        "已经",
        "已",
        "应",
        "要求",
        "指导书",
        "依据",
        "条目",
    }

    def __init__(self) -> None:
        self.guidance_service = GuidanceService()
        self.repository = TemplateGuidebookLinkRepository()
        self.template_match_service = TemplateItemMatchService()

    def link_guidebook(self, db: Session, template_item_id: str) -> dict:
        template_item = self._get_template_item(db, template_item_id)
        guidance_items = self.guidance_service.list_items(db)["items"]
        if not guidance_items:
            raise BadRequestException("GUIDANCE_LIBRARY_EMPTY", "指导书依据库为空，请先导入指导书")

        matches = self._build_matches(template_item, guidance_items)
        links = [
            TemplateGuidebookLink(
                template_item_id=template_item.id,
                guidance_item_id=match["guidance_item"].id,
                match_score=match["match_score"],
                match_reason=match["match_reason"],
            )
            for match in matches
        ]
        self.repository.replace_for_template_item(db, template_item.id, links)
        db.commit()
        return {
            "template_item_id": template_item.id,
            "linked_count": len(links),
            "updated_count": len(links),
            "top_score": links[0].match_score if links else None,
        }

    def list_guidebook_links(self, db: Session, template_item_id: str) -> list[dict]:
        self._get_template_item(db, template_item_id)
        rows = self.repository.list_guidebook_by_template_item(db, template_item_id)
        return [self._serialize_link(link, guidance_item) for link, guidance_item in rows]

    def _build_matches(self, template_item: AssessmentTemplateItem, guidance_items: list[GuidanceItem]) -> list[dict]:
        results: list[dict] = []
        for guidance_item in guidance_items:
            match = self._score_guidance_item(template_item, guidance_item)
            if match is None:
                continue
            results.append(match)
        return sorted(
            results,
            key=lambda item: (-item["match_score"], item["guidance_item"].section_path, item["guidance_item"].created_at),
        )[: self.TOP_N]

    def _score_guidance_item(self, template_item: AssessmentTemplateItem, guidance_item: GuidanceItem) -> dict | None:
        score = 0.0
        summary: list[str] = []

        section_text = " ".join(
            [
                guidance_item.section_title or "",
                guidance_item.section_path or "",
                guidance_item.plain_text or "",
            ]
        )
        evidence_text = " ".join(guidance_item.evidence_requirements_json or [])
        guidance_asset_type = self._infer_guidance_asset_type(guidance_item)
        template_asset_type = self._infer_template_asset_type(template_item)
        template_item_no = self._extract_item_no(template_item.item_text or "")
        guidance_item_no = self._extract_item_no(guidance_item.plain_text or "")
        metadata = self._build_template_metadata(template_item)

        control_point_hits = self._collect_hits(section_text, [template_item.control_point])
        if control_point_hits:
            score += 0.35
            summary.append("控制点命中指导书章节")

        item_text_hits = self._collect_hits(guidance_item.plain_text, [template_item.item_text])
        if item_text_hits:
            score += 0.25
            summary.append("测评项命中指导书正文")
        else:
            partial_item_hits = self._collect_hits(guidance_item.plain_text, self._extract_tokens(template_item.item_text or ""))
            if partial_item_hits:
                score += min(0.2, 0.08 + len(partial_item_hits) * 0.04)
                summary.append(f"测评项关键词重合 {len(partial_item_hits)} 个")
                item_text_hits = partial_item_hits

        evidence_hits = self._collect_hits(
            evidence_text,
            metadata["page_keywords"] + metadata["command_keywords"] + metadata["fact_keywords"] + self._as_string_list(template_item.evidence_keywords_json),
        )
        if evidence_hits:
            score += min(0.2, 0.08 + len(evidence_hits) * 0.04)
            summary.append(f"证据要求命中模板证据关键词 {len(evidence_hits)} 个")

        if template_asset_type and guidance_asset_type and template_asset_type == guidance_asset_type:
            score += 0.12
            summary.append("对象类型命中指导书资产类型")

        if template_item_no and guidance_item_no and template_item_no == guidance_item_no:
            score += 0.08
            summary.append("条目序号命中")

        if score <= 0:
            return None

        return {
            "guidance_item": guidance_item,
            "match_score": round(min(score, 0.99), 2),
            "match_reason": {
                "summary": summary,
                "template_item_id": template_item.id,
                "guidance_item_id": guidance_item.id,
                "template_object_type": template_item.object_type,
                "template_object_category": template_item.object_category,
                "guidance_asset_type": guidance_asset_type,
                "control_point_hits": control_point_hits[:8],
                "item_text_hits": item_text_hits[:8],
                "evidence_hits": evidence_hits[:8],
                "item_no_match": template_item_no if template_item_no and template_item_no == guidance_item_no else None,
            },
        }

    def _serialize_link(self, link: TemplateGuidebookLink, guidance_item: GuidanceItem) -> dict:
        return {
            "template_item_id": link.template_item_id,
            "guidance_item_id": guidance_item.id,
            "match_score": link.match_score,
            "match_reason": link.match_reason,
            "guidance_item": guidance_item,
            "section_title": guidance_item.section_title,
            "section_path": guidance_item.section_path,
            "guidance_code": guidance_item.guidance_code,
            "check_points": guidance_item.check_points_json or [],
            "evidence_requirements": guidance_item.evidence_requirements_json or [],
            "record_suggestion": guidance_item.record_suggestion,
        }

    def _get_template_item(self, db: Session, template_item_id: str) -> AssessmentTemplateItem:
        item = db.get(AssessmentTemplateItem, template_item_id)
        if not item:
            raise NotFoundException("ASSESSMENT_TEMPLATE_ITEM_NOT_FOUND", "测评记录模板项不存在")
        return item

    def _build_template_metadata(self, item: AssessmentTemplateItem) -> dict[str, list[str]]:
        record_template = item.record_template or ""
        return {
            "page_keywords": self.template_match_service._extract_page_keywords(record_template, self._as_string_list(item.page_types_json)),
            "command_keywords": self.template_match_service._extract_command_keywords(record_template),
            "fact_keywords": self.template_match_service._extract_fact_keywords(record_template) + self._as_string_list(item.required_facts_json),
        }

    def _infer_template_asset_type(self, item: AssessmentTemplateItem) -> str | None:
        return self.template_match_service._infer_template_asset_type(item)

    def _infer_guidance_asset_type(self, guidance_item: GuidanceItem) -> str | None:
        content = " ".join(
            [
                guidance_item.section_title or "",
                guidance_item.section_path or "",
                guidance_item.plain_text or "",
                guidance_item.record_suggestion or "",
            ]
        ).lower()
        for keyword, asset_type in (
            ("防火墙", "firewall"),
            ("firewall", "firewall"),
            ("交换机", "switch"),
            ("switch", "switch"),
            ("windows", "server"),
            ("linux", "server"),
            ("服务器", "server"),
            ("数据库", "database"),
            ("mysql", "database"),
            ("oracle", "database"),
            ("中间件", "middleware"),
            ("tomcat", "middleware"),
            ("nginx", "middleware"),
            ("应用系统", "application"),
            ("安全管理", "management"),
            ("管理平台", "management"),
        ):
            if keyword in content:
                return asset_type
        return None

    def _extract_item_no(self, text: str) -> str | None:
        match = re.search(r"([a-d])\s*[\)）.]", (text or "").lower())
        return match.group(1) if match else None

    def _extract_tokens(self, text: str) -> list[str]:
        counter: Counter[str] = Counter()
        for token in self.TOKEN_PATTERN.findall(text or ""):
            normalized = self._normalize(token)
            if len(normalized) < 2 or normalized in self.STOPWORDS:
                continue
            counter[str(token).strip()] += 1
        return [token for token, _ in counter.most_common(12)]

    def _collect_hits(self, source_text: str, candidates: list[str | None]) -> list[str]:
        normalized_source = self._normalize(source_text)
        if len(normalized_source) < 2:
            return []
        hits: list[str] = []
        for candidate in candidates:
            normalized_candidate = self._normalize(candidate)
            if len(normalized_candidate) < 2:
                continue
            if normalized_candidate in normalized_source or normalized_source in normalized_candidate:
                if str(candidate) not in hits:
                    hits.append(str(candidate))
        return hits

    def _as_string_list(self, value) -> list[str]:
        return [str(item) for item in value] if isinstance(value, list) else []

    def _normalize(self, value: str | None) -> str:
        return re.sub(r"\s+", "", (value or "").strip().lower())
