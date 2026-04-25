from app.core.exceptions import NotFoundException
from app.models.asset import Asset
from app.repositories.asset_repository import AssetRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.asset import AssetCreate, AssetUpdate


class AssetService:
    def __init__(self) -> None:
        self.repository = AssetRepository()
        self.project_repository = ProjectRepository()

    def list_project_assets(self, db, project_id: str):
        self._ensure_project_exists(db, project_id)
        return self.repository.list_by_project(db, project_id)

    def get_asset(self, db, asset_id: str):
        asset = self.repository.get(db, asset_id)
        if not asset:
            raise NotFoundException("ASSET_NOT_FOUND", "文件资产不存在")
        return asset

    def create_project_asset(self, db, project_id: str, payload: AssetCreate):
        self._ensure_project_exists(db, project_id)
        data = payload.model_dump()
        data["project_id"] = project_id
        data["asset_kind"] = data.get("asset_kind") or "test_object"
        asset = Asset(**data)
        return self.repository.create(db, asset)

    def update_asset(self, db, asset_id: str, payload: AssetUpdate):
        asset = self.get_asset(db, asset_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(asset, key, value)
        return self.repository.update(db, asset)

    def delete_asset(self, db, asset_id: str):
        asset = self.get_asset(db, asset_id)
        self.repository.delete(db, asset)

    def _ensure_project_exists(self, db, project_id: str) -> None:
        if not self.project_repository.get(db, project_id):
            raise NotFoundException("PROJECT_NOT_FOUND", "项目不存在")
