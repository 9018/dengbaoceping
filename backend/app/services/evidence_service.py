from __future__ import annotations

import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException, StorageException
from app.models.asset import Asset
from app.models.evidence import Evidence
from app.repositories.asset_repository import AssetRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.evidence import EvidenceUploadData


class EvidenceService:
    def __init__(self) -> None:
        self.repository = EvidenceRepository()
        self.asset_repository = AssetRepository()
        self.project_repository = ProjectRepository()

    def list_project_evidences(self, db, project_id: str):
        self._ensure_project_exists(db, project_id)
        return self.repository.list_by_project(db, project_id)

    def get_evidence(self, db, evidence_id: str):
        evidence = self.repository.get(db, evidence_id)
        if not evidence:
            raise NotFoundException("EVIDENCE_NOT_FOUND", "证据不存在")
        return evidence

    def delete_evidence(self, db, evidence_id: str):
        evidence = self.get_evidence(db, evidence_id)
        asset = evidence.asset
        self.repository.delete(db, evidence)
        if asset:
            self._remove_file(asset.absolute_path)
            self.asset_repository.delete(db, asset)

    def upload_project_evidence(self, db, project_id: str, upload: UploadFile, payload: EvidenceUploadData):
        self._ensure_project_exists(db, project_id)
        if not upload.filename:
            raise BadRequestException("EMPTY_FILENAME", "上传文件名不能为空")

        upload_dir = Path(settings.UPLOAD_DIR) / project_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        original_name = Path(upload.filename).name
        suffix = Path(original_name).suffix
        stored_name = f"{uuid4().hex}{suffix}"
        absolute_path = upload_dir / stored_name

        hasher = hashlib.sha256()
        size = 0
        try:
            with absolute_path.open("wb") as target:
                while chunk := upload.file.read(1024 * 1024):
                    size += len(chunk)
                    hasher.update(chunk)
                    target.write(chunk)
        except OSError as exc:
            raise StorageException("FILE_UPLOAD_FAILED", "文件保存失败", str(exc)) from exc
        finally:
            upload.file.close()

        mime_type = upload.content_type or mimetypes.guess_type(original_name)[0]
        relative_path = str(Path("uploads") / project_id / stored_name)
        modified_at = datetime.fromtimestamp(absolute_path.stat().st_mtime)

        asset = Asset(
            project_id=project_id,
            asset_kind="evidence_file",
            category=payload.category,
            category_label=payload.category_label,
            batch_no=datetime.now().strftime("%Y%m%d%H%M%S"),
            filename=original_name,
            primary_ip=None,
            file_ext=suffix or None,
            mime_type=mime_type,
            relative_path=relative_path,
            absolute_path=str(absolute_path),
            file_size=size,
            file_sha256=hasher.hexdigest(),
            file_mtime=modified_at,
            source="upload",
            ingest_status="stored",
        )
        asset = self.asset_repository.create(db, asset)

        evidence = Evidence(
            project_id=project_id,
            asset_id=asset.id,
            matched_asset_id=None,
            matched_guidance_id=None,
            evidence_type=payload.evidence_type,
            title=payload.title or original_name,
            summary=payload.summary,
            text_content=payload.text_content,
            ocr_result_json=None,
            ocr_status=None,
            ocr_provider=None,
            ocr_processed_at=None,
            device=payload.device,
            ports_json=payload.ports_json,
            evidence_time=payload.evidence_time,
            tags_json=payload.tags_json,
            source_ref=payload.source_ref,
            asset_match_score=None,
            asset_match_reasons_json=None,
            asset_match_status="pending",
            guidance_match_score=None,
            guidance_match_reasons_json=None,
            guidance_match_status="pending",
        )
        return self.repository.create(db, evidence)

    def _ensure_project_exists(self, db, project_id: str) -> None:
        if not self.project_repository.get(db, project_id):
            raise NotFoundException("PROJECT_NOT_FOUND", "项目不存在")

    def _remove_file(self, absolute_path: str | None) -> None:
        if not absolute_path:
            return
        path = Path(absolute_path)
        if path.exists():
            path.unlink()
            parent = path.parent
            upload_root = Path(settings.UPLOAD_DIR)
            if parent.exists() and parent != upload_root:
                try:
                    parent.rmdir()
                except OSError:
                    pass
