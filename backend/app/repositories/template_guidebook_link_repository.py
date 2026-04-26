from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.assessment_template import TemplateGuidebookLink
from app.models.guidance_item import GuidanceItem


class TemplateGuidebookLinkRepository:
    def replace_for_template_item(
        self,
        db: Session,
        template_item_id: str,
        links: list[TemplateGuidebookLink],
    ) -> list[TemplateGuidebookLink]:
        db.query(TemplateGuidebookLink).filter(TemplateGuidebookLink.template_item_id == template_item_id).delete()
        if links:
            db.add_all(links)
            db.flush()
        return links

    def list_guidebook_by_template_item(self, db: Session, template_item_id: str):
        return (
            db.query(TemplateGuidebookLink, GuidanceItem)
            .join(GuidanceItem, GuidanceItem.id == TemplateGuidebookLink.guidance_item_id)
            .filter(TemplateGuidebookLink.template_item_id == template_item_id)
            .order_by(TemplateGuidebookLink.match_score.desc(), GuidanceItem.section_path.asc(), GuidanceItem.created_at.asc())
            .all()
        )
