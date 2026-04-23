from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.asset import Asset


class AssetRepository:
    def list(self, db: Session) -> list[Asset]:
        return db.query(Asset).order_by(Asset.created_at.desc()).all()

    def list_by_project(self, db: Session, project_id: str) -> list[Asset]:
        return db.query(Asset).filter(Asset.project_id == project_id).order_by(Asset.created_at.desc()).all()

    def get(self, db: Session, asset_id: str) -> Asset | None:
        return db.get(Asset, asset_id)

    def create(self, db: Session, asset: Asset) -> Asset:
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    def update(self, db: Session, asset: Asset) -> Asset:
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    def delete(self, db: Session, asset: Asset) -> None:
        db.delete(asset)
        db.commit()
