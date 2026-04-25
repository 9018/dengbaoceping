from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.guidance_history_link import GuidanceHistoryLink
from app.models.guidance_item import GuidanceItem
from app.models.history_record import HistoryRecord


class GuidanceHistoryLinkRepository:
    def replace_for_guidance(
        self,
        db: Session,
        guidance_item_id: str,
        links: list[GuidanceHistoryLink],
    ) -> list[GuidanceHistoryLink]:
        db.query(GuidanceHistoryLink).filter(GuidanceHistoryLink.guidance_item_id == guidance_item_id).delete()
        if links:
            db.add_all(links)
            db.flush()
        return links

    def list_history_by_guidance(
        self,
        db: Session,
        guidance_item_id: str,
        compliance_status: str | None = None,
    ):
        query = (
            db.query(GuidanceHistoryLink, HistoryRecord)
            .join(HistoryRecord, HistoryRecord.id == GuidanceHistoryLink.history_record_id)
            .filter(GuidanceHistoryLink.guidance_item_id == guidance_item_id)
        )
        if compliance_status:
            query = query.filter(HistoryRecord.compliance_status == compliance_status)
        return query.order_by(GuidanceHistoryLink.match_score.desc(), HistoryRecord.created_at.desc(), HistoryRecord.row_index.asc()).all()

    def list_guidance_by_history(self, db: Session, history_record_id: str):
        return (
            db.query(GuidanceHistoryLink, GuidanceItem)
            .join(GuidanceItem, GuidanceItem.id == GuidanceHistoryLink.guidance_item_id)
            .filter(GuidanceHistoryLink.history_record_id == history_record_id)
            .order_by(GuidanceHistoryLink.match_score.desc(), GuidanceItem.section_path.asc(), GuidanceItem.created_at.asc())
            .all()
        )
