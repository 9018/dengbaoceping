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
        asset_name: str | None = None,
        item_text: str | None = None,
        compliance_result: str | None = None,
        keyword: str | None = None,
        project_name: str | None = None,
        asset_ip: str | None = None,
        standard_type: str | None = None,
        item_code: str | None = None,
    ) -> list[HistoryRecord]:
        query = db.query(HistoryRecord)
        if sheet_name:
            query = query.filter(HistoryRecord.sheet_name == sheet_name)
        if control_point:
            query = query.filter(HistoryRecord.control_point.ilike(f"%{control_point}%"))
        if compliance_status:
            query = query.filter(HistoryRecord.compliance_status == compliance_status)
        if asset_type:
            query = query.filter(HistoryRecord.asset_type == asset_type)
        if asset_name:
            query = query.filter(HistoryRecord.asset_name.ilike(f"%{asset_name}%"))
        if item_text:
            query = query.filter(
                HistoryRecord.item_text.ilike(f"%{item_text}%") | HistoryRecord.evaluation_item.ilike(f"%{item_text}%")
            )
        if compliance_result:
            query = query.filter(HistoryRecord.compliance_result == compliance_result)
        if project_name:
            query = query.filter(HistoryRecord.project_name.ilike(f"%{project_name}%"))
        if asset_ip:
            query = query.filter(HistoryRecord.asset_ip.ilike(f"%{asset_ip}%"))
        if standard_type:
            query = query.filter(HistoryRecord.standard_type.ilike(f"%{standard_type}%"))
        if item_code:
            query = query.filter(HistoryRecord.item_code.ilike(f"%{item_code}%") | HistoryRecord.item_no.ilike(f"%{item_code}%"))
        if keyword:
            query = query.filter(self._keyword_filter(keyword))
        return query.order_by(HistoryRecord.created_at.desc(), HistoryRecord.row_index.asc()).all()

    def get(self, db: Session, record_id: str) -> HistoryRecord | None:
        return db.get(HistoryRecord, record_id)

    def count(self, db: Session) -> int:
        return db.query(func.count(HistoryRecord.id)).scalar() or 0

    def count_distinct_sheets(self, db: Session) -> int:
        return db.query(func.count(func.distinct(HistoryRecord.sheet_name))).scalar() or 0

    def list_by_keyword(self, db: Session, keyword: str) -> list[HistoryRecord]:
        return (
            db.query(HistoryRecord)
            .filter(self._keyword_filter(keyword))
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

    def _keyword_filter(self, keyword: str):
        normalized = f"%{keyword.lower()}%"
        return (
            func.lower(func.coalesce(HistoryRecord.source_file, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.project_name, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.sheet_name, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.asset_name, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.asset_ip, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.asset_type, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.standard_type, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.control_point, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.item_text, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.evaluation_item, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.raw_text, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.record_text, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.compliance_result, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.compliance_status, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.item_code, "")).like(normalized)
            | func.lower(func.coalesce(HistoryRecord.item_no, "")).like(normalized)
        )
