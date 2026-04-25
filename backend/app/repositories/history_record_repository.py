from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.history_record import HistoryRecord


class HistoryRecordRepository:
    def create_many(self, db: Session, records: list[HistoryRecord]) -> list[HistoryRecord]:
        db.add_all(records)
        db.flush()
        return records

    def list_records(
        self,
        db: Session,
        *,
        sheet_name: str | None = None,
        control_point: str | None = None,
        compliance_status: str | None = None,
        asset_type: str | None = None,
    ) -> list[HistoryRecord]:
        query = db.query(HistoryRecord)
        if sheet_name:
            query = query.filter(HistoryRecord.sheet_name == sheet_name)
        if control_point:
            query = query.filter(HistoryRecord.control_point == control_point)
        if compliance_status:
            query = query.filter(HistoryRecord.compliance_status == compliance_status)
        if asset_type:
            query = query.filter(HistoryRecord.asset_type == asset_type)
        return query.order_by(HistoryRecord.created_at.desc(), HistoryRecord.row_index.asc()).all()

    def get(self, db: Session, record_id: str) -> HistoryRecord | None:
        return db.get(HistoryRecord, record_id)

    def count(self, db: Session) -> int:
        return db.query(func.count(HistoryRecord.id)).scalar() or 0

    def count_distinct_sheets(self, db: Session) -> int:
        return db.query(func.count(func.distinct(HistoryRecord.sheet_name))).scalar() or 0

    def list_by_keyword(self, db: Session, keyword: str) -> list[HistoryRecord]:
        normalized = f"%{keyword.lower()}%"
        return (
            db.query(HistoryRecord)
            .filter(
                func.lower(func.coalesce(HistoryRecord.sheet_name, "")).like(normalized)
                | func.lower(func.coalesce(HistoryRecord.asset_name, "")).like(normalized)
                | func.lower(func.coalesce(HistoryRecord.control_point, "")).like(normalized)
                | func.lower(func.coalesce(HistoryRecord.evaluation_item, "")).like(normalized)
                | func.lower(func.coalesce(HistoryRecord.record_text, "")).like(normalized)
                | func.lower(func.coalesce(HistoryRecord.item_no, "")).like(normalized)
            )
            .order_by(HistoryRecord.created_at.desc(), HistoryRecord.row_index.asc())
            .all()
        )

    def list_all(self, db: Session) -> list[HistoryRecord]:
        return db.query(HistoryRecord).order_by(HistoryRecord.created_at.desc(), HistoryRecord.row_index.asc()).all()

    def group_by_status(self, db: Session) -> list[tuple[str | None, int]]:
        return (
            db.query(HistoryRecord.compliance_status, func.count(HistoryRecord.id))
            .group_by(HistoryRecord.compliance_status)
            .all()
        )

    def group_by_asset_type(self, db: Session) -> list[tuple[str | None, int]]:
        return (
            db.query(HistoryRecord.asset_type, func.count(HistoryRecord.id))
            .group_by(HistoryRecord.asset_type)
            .all()
        )
