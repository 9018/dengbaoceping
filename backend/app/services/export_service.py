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


EXPORTABLE_RECORD_STATUS = {"approved", "exported"}


class ExportService:
    def __init__(self) -> None:
        self.project_repository = ProjectRepository()
        self.record_repository = EvaluationRecordRepository()
        self.export_job_repository = ExportJobRepository()

    def create_project_export(self, db: Session, project_id: str, export_format: str = "txt") -> ExportJob:
        project = self.project_repository.get(db, project_id)
        if not project:
            raise NotFoundException("PROJECT_NOT_FOUND", "项目不存在")
        if export_format != "txt":
            raise BadRequestException("EXPORT_FORMAT_NOT_SUPPORTED", "当前仅支持TXT导出")

        records = self.record_repository.list_by_project(db, project_id)
        not_ready_record_ids = [record.id for record in records if record.status not in EXPORTABLE_RECORD_STATUS]
        if not_ready_record_ids:
            raise BadRequestException(
                "RECORD_NOT_READY_FOR_EXPORT",
                "存在未完成审批的测评记录，无法导出",
                {"record_ids": not_ready_record_ids, "allowed_statuses": sorted(EXPORTABLE_RECORD_STATUS)},
            )
        for record in records:
            if record.status == "approved":
                record.status = "exported"

        content = self._render_txt(project.name, records)
        export_dir = Path(settings.EXPORT_DIR)
        export_dir.mkdir(parents=True, exist_ok=True)
        safe_project_name = project.name.replace("/", "-").replace("\\", "-").strip() or "project"
        file_name = f"{safe_project_name}_{project_id[:8]}_export.txt"
        file_path = export_dir / file_name
        file_path.write_text(content, encoding="utf-8")

        export_job = ExportJob(
            project_id=project_id,
            format=export_format,
            status="completed",
            file_name=file_name,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            record_count=len(records),
        )
        self.export_job_repository.create(db, export_job)
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
        return FileResponse(path=file_path, media_type="text/plain; charset=utf-8", filename=export_job.file_name)


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
