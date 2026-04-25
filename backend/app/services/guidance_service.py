from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.guidance_item import GuidanceItem
from app.services.guidance_parser import GuidanceParser


class GuidanceService:
    def __init__(self) -> None:
        self.parser = GuidanceParser()

    @property
    def source_file(self) -> str:
        return "md/指导书.md"

    @property
    def guidance_path(self) -> Path:
        return Path(settings.GUIDANCE_FILE_PATH)

    def get_library_status(self, db: Session) -> dict:
        file_info = self._read_file_state()
        total = self._count_items(db)
        return {
            "source_file": self.source_file,
            "absolute_path": str(self.guidance_path),
            "file_exists": file_info["file_exists"],
            "file_empty": file_info["file_empty"],
            "file_message": file_info["message"],
            "imported": total > 0,
            "total": total,
        }

    def import_markdown(self, db: Session) -> dict:
        file_info = self._read_file_state(raise_on_error=True)
        if file_info["file_empty"]:
            raise BadRequestException("GUIDANCE_MD_EMPTY", "指导书.md 当前为空，请先补充内容")

        sections = self.parser.parse(self.guidance_path, self.source_file)
        if not sections:
            raise BadRequestException("GUIDANCE_MD_NO_SECTIONS", "指导书未识别到可导入的 Markdown 标题章节")

        db.query(GuidanceItem).filter(GuidanceItem.source_file == self.source_file).delete()
        for section in sections:
            db.add(GuidanceItem(**asdict(section)))
        db.commit()

        return {
            **self.get_library_status(db),
            "imported_count": len(sections),
        }

    def list_items(self, db: Session, keyword: str | None = None) -> dict:
        items = self._load_items(db)
        if keyword:
            items = [item for item in items if self._matches_keyword(item, keyword)]
        return {
            **self.get_library_status(db),
            "keyword": keyword,
            "items": items,
        }

    def get_item(self, db: Session, guidance_id: str) -> GuidanceItem:
        item = db.get(GuidanceItem, guidance_id)
        if not item:
            raise NotFoundException("GUIDANCE_ITEM_NOT_FOUND", "指导书章节不存在")
        return item

    def search_items(self, db: Session, keyword: str) -> list[GuidanceItem]:
        normalized = keyword.strip()
        if not normalized:
            raise BadRequestException("GUIDANCE_KEYWORD_REQUIRED", "请输入搜索关键词")
        items = self._load_items(db)
        return [item for item in items if self._matches_keyword(item, normalized)]

    def _load_items(self, db: Session) -> list[GuidanceItem]:
        stmt = select(GuidanceItem).order_by(GuidanceItem.section_path.asc(), GuidanceItem.created_at.asc())
        return list(db.scalars(stmt).all())

    def _count_items(self, db: Session) -> int:
        return len(self._load_items(db))

    def _matches_keyword(self, item: GuidanceItem, keyword: str) -> bool:
        normalized = keyword.strip().lower()
        haystacks = [
            item.guidance_code,
            item.section_path,
            item.section_title,
            item.level1,
            item.level2,
            item.level3,
            item.plain_text,
            item.record_suggestion,
            " ".join(item.keywords_json or []),
            " ".join(item.check_points_json or []),
            " ".join(item.evidence_requirements_json or []),
        ]
        return any(normalized in (value or "").lower() for value in haystacks)

    def _read_file_state(self, raise_on_error: bool = False) -> dict:
        if not self.guidance_path.exists():
            if raise_on_error:
                raise NotFoundException("GUIDANCE_MD_NOT_FOUND", "指导书文件不存在，请确认 md/指导书.md 已就位")
            return {"file_exists": False, "file_empty": False, "message": "指导书文件不存在，请确认 md/指导书.md 已就位"}

        content = self.guidance_path.read_text(encoding="utf-8")
        if not content.strip():
            return {"file_exists": True, "file_empty": True, "message": "指导书.md 当前为空，请先补充内容"}

        return {"file_exists": True, "file_empty": False, "message": "指导书文件已就绪"}
