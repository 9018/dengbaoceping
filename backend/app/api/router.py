from fastapi import APIRouter

from app.api.v1.endpoints import assessment_template_items, assessment_templates, assets, evidences, exports, fields, guidance, history, history_records, project_templates, projects, records, workflow

api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(project_templates.router)
api_router.include_router(assessment_templates.router)
api_router.include_router(assessment_template_items.router)
api_router.include_router(assets.router)
api_router.include_router(evidences.router)
api_router.include_router(fields.router)
api_router.include_router(records.router)
api_router.include_router(exports.router)
api_router.include_router(history.router)
api_router.include_router(history_records.router)
api_router.include_router(guidance.router)
api_router.include_router(workflow.router)
