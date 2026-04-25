from __future__ import annotations

from pathlib import Path

from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.export_job import ExportJob
from app.repositories.export_job_repository import ExportJobRepository
from app.repositories.evaluation_record_repository import EvaluationRecordRepository
from app.repositories.project_repository import ProjectRepository
from app.services.excel_export_service import ExcelExportService


EXPORTABLE_RECORD_STATUS = {"approved", "exported"}
EXCEL_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ExportService:
    def __init__(self) -> None:
        self.project_repository = ProjectRepository()
        self.record_repository = EvaluationRecordRepository()
        self.export_job_repository = ExportJobRepository()
        self.excel_export_service = ExcelExportService()

    def create_project_export(self, db: Session, project_id: str, export_format: str = "txt") -> ExportJob:
        project = self.project_repository.get(db, project_id)
        if not project:
            raise NotFoundException("PROJECT_NOT_FOUND", "项目不存在")
        if export_format != "txt":
            raise BadRequestException("EXPORT_FORMAT_NOT_SUPPORTED", "当前仅支持TXT导出")

        records = self.record_repository.list_by_project(db, project_id)
        self._ensure_records_ready(records)
        self._mark_records_exported(records)

        content = self._render_txt(project.name, records)
        export_dir = self._get_export_dir()
        safe_project_name = self._build_safe_project_name(project.name)
        file_name = f"{safe_project_name}_{project_id[:8]}_export.txt"
        file_path = export_dir / file_name
        file_path.write_text(content, encoding="utf-8")
        export_job = self._create_export_job(db, project_id, "txt", None, file_name, file_path, len(records))
        db.commit()
        db.refresh(export_job)
        return export_job

    def create_project_excel_export(self, db: Session, project_id: str, mode: str = "official") -> ExportJob:
        project = self.project_repository.get(db, project_id)
        if not project:
            raise NotFoundException("PROJECT_NOT_FOUND", "项目不存在")
        if mode not in {"official", "debug"}:
            raise BadRequestException("EXPORT_MODE_NOT_SUPPORTED", "导出模式不支持", {"allowed_modes": ["debug", "official"]})

        records = self.record_repository.list_by_project_for_export(db, project_id)
        self._ensure_records_ready(records)
        self._mark_records_exported(records)

        content = self.excel_export_service.build_workbook(db, records, mode)
        export_dir = self._get_export_dir()
        safe_project_name = self._build_safe_project_name(project.name)
        file_name = f"{safe_project_name}_{project_id[:8]}_{mode}.xlsx"
        file_path = export_dir / file_name
        file_path.write_bytes(content)
        export_job = self._create_export_job(db, project_id, "xlsx", mode, file_name, file_path, len(records))
        db.commit()
        db.refresh(export_job)
        return export_job

    def list_project_exports(self, db: Session, project_id: str) -> list[ExportJob]:
        project = self.project_repository.get(db, project_id)
        if not project:
            raise NotFoundException("PROJECT_NOT_FOUND", "项目不存在")
        return self.export_job_repository.list_by_project(db, project_id)

    def download_export(self, db: Session, export_id: str) -> FileResponse:
        export_job = self.export_job_repository.get(db, export_id)
        if not export_job:
            raise NotFoundException("EXPORT_NOT_FOUND", "导出任务不存在")
        file_path = Path(export_job.file_path)
        if not file_path.exists():
            raise NotFoundException("EXPORT_FILE_NOT_FOUND", "导出文件不存在")
        return FileResponse(path=file_path, media_type=self._resolve_media_type(export_job.format), filename=export_job.file_name)

    def _create_export_job(
        self,
        db: Session,
        project_id: str,
        export_format: str,
        mode: str | None,
        file_name: str,
        file_path: Path,
        record_count: int,
    ) -> ExportJob:
        export_job = ExportJob(
            project_id=project_id,
            format=export_format,
            mode=mode,
            status="completed",
            file_name=file_name,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            record_count=record_count,
        )
        self.export_job_repository.create(db, export_job)
        return export_job

    def _get_export_dir(self) -> Path:
        export_dir = Path(settings.EXPORT_DIR)
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir

    def _build_safe_project_name(self, project_name: str) -> str:
        return project_name.replace("/", "-").replace("\\", "-").strip() or "project"

    def _ensure_records_ready(self, records: list) -> None:
        not_ready_record_ids = [record.id for record in records if record.status not in EXPORTABLE_RECORD_STATUS]
        if not_ready_record_ids:
            raise BadRequestException(
                "RECORD_NOT_READY_FOR_EXPORT",
                "存在未完成审批的测评记录，无法导出",
                {"record_ids": not_ready_record_ids, "allowed_statuses": sorted(EXPORTABLE_RECORD_STATUS)},
            )

    def _mark_records_exported(self, records: list) -> None:
        for record in records:
            if record.status == "approved":
                record.status = "exported"

    def _resolve_media_type(self, export_format: str) -> str:
        if export_format == "xlsx":
            return EXCEL_MEDIA_TYPE
        return "text/plain; charset=utf-8"

    def _render_txt(self, project_name: str, records: list) -> str:
        grouped_records: dict[str, list] = {}
        for record in reversed(records):
            device_name = self._resolve_device_name(record)
            grouped_records.setdefault(device_name, []).append(record)

        lines = [f"项目：{project_name}"]
        if not grouped_records:
            lines.append("\n设备：未分组")
            lines.append("  无测评记录")
            return "\n".join(lines) + "\n"

        for device_name, device_records in grouped_records.items():
            lines.append(f"\n设备：{device_name}")
            for index, record in enumerate(device_records, start=1):
                title = record.title or "未命名记录"
                content = record.final_content or record.record_text or ""
                status = record.status
                lines.append(f"  {index}. {title}")
                lines.append(f"     内容：{content}")
                lines.append(f"     状态：{status}")
        return "\n".join(lines) + "\n"

    def _resolve_device_name(self, record) -> str:
        for link in getattr(record, "evidence_links", []):
            evidence = getattr(link, "evidence", None)
            if evidence and evidence.device:
                return evidence.device
        return "未命名设备"
