from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.asset import AssetCreateRequest, AssetCreate, AssetUpdate
from app.schemas.common import ApiResponse, list_response, success_response
from app.services.asset_service import AssetService

router = APIRouter(tags=["assets"])
service = AssetService()


@router.get("/projects/{project_id}/assets", response_model=ApiResponse)
def list_assets(project_id: str, db: Session = Depends(get_db)):
    return list_response(service.list_project_assets(db, project_id))


@router.post("/projects/{project_id}/assets", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_asset(project_id: str, payload: AssetCreateRequest, db: Session = Depends(get_db)):
    asset = service.create_project_asset(db, project_id, AssetCreate(project_id=project_id, **payload.model_dump()))
    return success_response(asset, "文件资产创建成功")


@router.get("/assets/{asset_id}", response_model=ApiResponse)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    return success_response(service.get_asset(db, asset_id))


@router.put("/assets/{asset_id}", response_model=ApiResponse)
def update_asset(asset_id: str, payload: AssetUpdate, db: Session = Depends(get_db)):
    return success_response(service.update_asset(db, asset_id, payload), "文件资产更新成功")


@router.delete("/assets/{asset_id}", response_model=ApiResponse)
def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    service.delete_asset(db, asset_id)
    return success_response(message="文件资产已删除")
