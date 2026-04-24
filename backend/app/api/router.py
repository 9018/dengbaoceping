from fastapi import APIRouter

from app.api.v1.endpoints import assets, evidences, exports, fields, projects, records

api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(assets.router)
api_router.include_router(evidences.router)
api_router.include_router(fields.router)
api_router.include_router(records.router)
api_router.include_router(exports.router)
