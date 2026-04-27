from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.history_record_repository import HistoryRecordRepository
from app.schemas.common import ApiResponse, paged_response, success_response
from app.schemas.project import ProjectAssessmentItemRead, ProjectAssessmentTableRead, WorkflowNextActionRead, WorkflowProjectStatusRead
from app.services.assessment_template_import_service import AssessmentTemplateImportService
from app.services.assessment_template_service import AssessmentTemplateService
from app.services.evidence_fact_service import EvidenceFactService
from app.services.guidance_service import GuidanceService
from app.services.history_import_service import HistoryImportService
from app.services.project_assessment_table_service import ProjectAssessmentTableService
from app.services.record_draft_service import RecordDraftService
from app.services.template_item_match_service import TemplateItemMatchService

router = APIRouter(tags=["workflow"])
assessment_template_import_service = AssessmentTemplateImportService()
assessment_template_service = AssessmentTemplateService()
guidance_service = GuidanceService()
history_import_service = HistoryImportService()
history_record_repository = HistoryRecordRepository()
project_assessment_table_service = ProjectAssessmentTableService()
evidence_fact_service = EvidenceFactService()
record_draft_service = RecordDraftService()
template_item_match_service = TemplateItemMatchService()


@router.get("/workflow/global-status", response_model=ApiResponse)
def get_global_status(db: Session = Depends(get_db)):
    workbooks = assessment_template_service.list_workbooks(db)
    guidance = guidance_service.list_items(db)
    history_total = history_record_repository.count(db)
    completed = bool(workbooks) and guidance["total"] > 0 and history_total > 0
    return success_response(
        {
            "template_workbook_count": len(workbooks),
            "template_item_count": sum(item.item_count for item in workbooks),
            "guidance_item_count": guidance["total"],
            "history_record_count": history_total,
            "canNext": bool(workbooks),
            "status": "completed" if completed else "ready" if workbooks else "not_started",
            "summary": "全局知识库状态汇总",
        },
        "全局流程状态获取成功",
    )


@router.post("/workflow/import-template", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def import_template(
    file: UploadFile = File(...),
    duplicate_policy: str = Query(default="skip"),
    db: Session = Depends(get_db),
):
    content = await file.read()
    result = assessment_template_import_service.import_excel(
        db,
        file.filename or "assessment_template.xlsx",
        content,
        duplicate_policy=duplicate_policy,
    )
    return success_response(result, "测评记录模板导入成功")


@router.post("/workflow/import-guidance", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def import_guidance(db: Session = Depends(get_db)):
    result = guidance_service.import_markdown(db)
    return success_response(result, "指导书导入成功")


@router.post("/workflow/import-history", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def import_history(
    file: UploadFile = File(...),
    duplicate_policy: str = Query(default="skip"),
    db: Session = Depends(get_db),
):
    content = await file.read()
    result = history_import_service.import_excel(db, file.filename or "history.xlsx", content, duplicate_policy=duplicate_policy)
    return success_response(result, "历史测评记录导入成功")


@router.get("/projects/{project_id}/workflow/status", response_model=ApiResponse)
def get_project_workflow_status(project_id: str, db: Session = Depends(get_db)):
    result = WorkflowProjectStatusRead.model_validate(project_assessment_table_service.get_project_workflow_status(db, project_id))
    return success_response(result, "项目流程状态获取成功")


@router.get("/projects/{project_id}/assessment-next-action", response_model=ApiResponse)
def get_project_assessment_next_action(project_id: str, db: Session = Depends(get_db)):
    result = WorkflowNextActionRead.model_validate(project_assessment_table_service.get_project_next_action(db, project_id))
    return success_response(result, "项目下一步动作获取成功")


@router.post("/projects/{project_id}/assets/{asset_id}/generate-assessment-table", response_model=ApiResponse)
def generate_project_assessment_table(project_id: str, asset_id: str, force: bool = Query(default=False), db: Session = Depends(get_db)):
    result = project_assessment_table_service.generate_for_asset(db, project_id, asset_id, force=force)
    return success_response(result, "项目测评表生成成功")


@router.get("/projects/{project_id}/assessment-tables", response_model=ApiResponse)
def list_project_assessment_tables(
    project_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    tables, total = project_assessment_table_service.list_project_tables_page(db, project_id, page=page, page_size=page_size)
    return paged_response(
        [ProjectAssessmentTableRead.model_validate(item) for item in tables],
        total,
        page,
        page_size,
        "项目测评表列表获取成功",
    )


@router.get("/assessment-tables/{table_id}/items", response_model=ApiResponse)
def list_project_assessment_items(
    table_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    items, total = project_assessment_table_service.list_table_items_page(db, table_id, page=page, page_size=page_size)
    return paged_response(
        [ProjectAssessmentItemRead.model_validate(item) for item in items],
        total,
        page,
        page_size,
        "项目测评项列表获取成功",
    )


@router.post("/evidences/{evidence_id}/extract-facts", response_model=ApiResponse)
def extract_evidence_facts(evidence_id: str, db: Session = Depends(get_db)):
    result = evidence_fact_service.classify_and_extract(db, evidence_id)
    return success_response(result, "证据事实识别完成")


@router.post("/evidences/{evidence_id}/match-project-assessment-item", response_model=ApiResponse)
def match_project_assessment_item(
    evidence_id: str,
    project_id: str = Query(...),
    asset_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    match_result = template_item_match_service.match(db, evidence_id)
    project_items = project_assessment_table_service.repository.list_items_by_project(db, project_id)
    if asset_id:
        project_items = [item for item in project_items if item.asset_id == asset_id]
    candidate_ids = {item.source_template_item_id: item for item in project_items if item.source_template_item_id}
    mapped = []
    for candidate in match_result.get("candidates") or []:
        project_item = candidate_ids.get(candidate.get("id"))
        if not project_item:
            continue
        mapped.append(
            {
                "project_assessment_item_id": project_item.id,
                "table_id": project_item.table_id,
                "sheet_name": project_item.sheet_name,
                "row_index": project_item.row_index,
                "item_code": project_item.item_code,
                "control_point": project_item.control_point,
                "item_text": project_item.item_text,
                "score": candidate.get("score"),
                "reasons": candidate.get("reasons") or [],
                "matched_keywords": candidate.get("matched_keywords") or [],
            }
        )
    return success_response(
        {
            "matched_project_assessment_item": mapped[0] if mapped else None,
            "candidates": mapped,
            "score": mapped[0]["score"] if mapped else 0,
            "confidence": match_result.get("confidence", 0),
            "reason": match_result.get("reason") or [],
        },
        "项目测评项匹配完成",
    )


@router.post("/project-assessment-items/{item_id}/generate-draft", response_model=ApiResponse)
def generate_project_assessment_draft(item_id: str, evidence_id: str = Query(...), db: Session = Depends(get_db)):
    result = record_draft_service.generate_draft(db, item_id, evidence_id)
    return success_response(result, "测评记录草稿生成成功")


@router.post("/project-assessment-items/{item_id}/confirm", response_model=ApiResponse)
def confirm_project_assessment_item(
    item_id: str,
    final_record_text: str | None = None,
    final_compliance_result: str | None = None,
    review_comment: str | None = None,
    reviewed_by: str | None = None,
    db: Session = Depends(get_db),
):
    result = project_assessment_table_service.confirm_item(
        db,
        item_id,
        final_record_text=final_record_text,
        final_compliance_result=final_compliance_result,
        review_comment=review_comment,
        reviewed_by=reviewed_by,
    )
    return success_response(result, "项目测评项确认成功")
