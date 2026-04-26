from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.assessment_template import TemplateHistoryLink
from app.models.history_record import HistoryRecord


class TemplateHistoryLinkRepository:
    def replace_for_template_item(
        self,
        db: Session,
        template_item_id: str,
        links: list[TemplateHistoryLink],
    ) -> list[TemplateHistoryLink]:
        db.query(TemplateHistoryLink).filter(TemplateHistoryLink.template_item_id == template_item_id).delete()
        if links:
            db.add_all(links)
            db.flush()
        return links

    def list_history_by_template_item(
        self,
        db: Session,
        template_item_id: str,
        compliance_result: str | None = None,
    ):
        query = (
            db.query(TemplateHistoryLink, HistoryRecord)
            .join(HistoryRecord, HistoryRecord.id == TemplateHistoryLink.history_record_id)
            .filter(TemplateHistoryLink.template_item_id == template_item_id)
        )
        if compliance_result:
            query = query.filter(
                (HistoryRecord.compliance_result == compliance_result)
                | (HistoryRecord.compliance_status == compliance_result)
            )
        return query.order_by(TemplateHistoryLink.match_score.desc(), HistoryRecord.created_at.desc(), HistoryRecord.row_index.asc()).all()
