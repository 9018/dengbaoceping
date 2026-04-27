from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.project_assessment_table import ProjectAssessmentItem, ProjectAssessmentTable


class ProjectAssessmentTableRepository:
    def list_by_project(self, db: Session, project_id: str) -> list[ProjectAssessmentTable]:
        return (
            db.query(ProjectAssessmentTable)
            .filter(ProjectAssessmentTable.project_id == project_id)
            .order_by(ProjectAssessmentTable.created_at.desc())
            .all()
        )

    def list_by_project_page(self, db: Session, project_id: str, *, page: int = 1, page_size: int = 20) -> tuple[list[ProjectAssessmentTable], int]:
        query = db.query(ProjectAssessmentTable).filter(ProjectAssessmentTable.project_id == project_id)
        total = query.count()
        items = query.order_by(ProjectAssessmentTable.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def list_by_project_and_asset(self, db: Session, project_id: str, asset_id: str) -> list[ProjectAssessmentTable]:
        return (
            db.query(ProjectAssessmentTable)
            .filter(ProjectAssessmentTable.project_id == project_id, ProjectAssessmentTable.asset_id == asset_id)
            .order_by(ProjectAssessmentTable.created_at.desc())
            .all()
        )

    def get(self, db: Session, table_id: str) -> ProjectAssessmentTable | None:
        return db.get(ProjectAssessmentTable, table_id)

    def get_by_project_and_asset(self, db: Session, project_id: str, asset_id: str) -> ProjectAssessmentTable | None:
        return (
            db.query(ProjectAssessmentTable)
            .filter(ProjectAssessmentTable.project_id == project_id, ProjectAssessmentTable.asset_id == asset_id)
            .first()
        )

    def create(self, db: Session, table: ProjectAssessmentTable) -> ProjectAssessmentTable:
        db.add(table)
        db.commit()
        db.refresh(table)
        return table

    def update(self, db: Session, table: ProjectAssessmentTable) -> ProjectAssessmentTable:
        db.add(table)
        db.commit()
        db.refresh(table)
        return table

    def delete(self, db: Session, table: ProjectAssessmentTable) -> None:
        db.delete(table)
        db.commit()

    def list_items(self, db: Session, table_id: str) -> list[ProjectAssessmentItem]:
        return (
            db.query(ProjectAssessmentItem)
            .filter(ProjectAssessmentItem.table_id == table_id)
            .order_by(ProjectAssessmentItem.sheet_name.asc(), ProjectAssessmentItem.row_index.asc())
            .all()
        )

    def list_items_page(self, db: Session, table_id: str, *, page: int = 1, page_size: int = 50) -> tuple[list[ProjectAssessmentItem], int]:
        query = db.query(ProjectAssessmentItem).filter(ProjectAssessmentItem.table_id == table_id)
        total = query.count()
        items = query.order_by(ProjectAssessmentItem.sheet_name.asc(), ProjectAssessmentItem.row_index.asc()).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def list_items_by_project(self, db: Session, project_id: str) -> list[ProjectAssessmentItem]:
        return (
            db.query(ProjectAssessmentItem)
            .filter(ProjectAssessmentItem.project_id == project_id)
            .order_by(ProjectAssessmentItem.sheet_name.asc(), ProjectAssessmentItem.row_index.asc())
            .all()
        )

    def list_items_by_project_and_asset(self, db: Session, project_id: str, asset_id: str) -> list[ProjectAssessmentItem]:
        return (
            db.query(ProjectAssessmentItem)
            .filter(ProjectAssessmentItem.project_id == project_id, ProjectAssessmentItem.asset_id == asset_id)
            .order_by(ProjectAssessmentItem.sheet_name.asc(), ProjectAssessmentItem.row_index.asc())
            .all()
        )

    def get_item(self, db: Session, item_id: str) -> ProjectAssessmentItem | None:
        return db.get(ProjectAssessmentItem, item_id)

    def create_items(self, db: Session, items: list[ProjectAssessmentItem]) -> list[ProjectAssessmentItem]:
        db.add_all(items)
        db.commit()
        for item in items:
            db.refresh(item)
        return items

    def update_item(self, db: Session, item: ProjectAssessmentItem) -> ProjectAssessmentItem:
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
