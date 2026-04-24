from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: str
    target_type: str
    target_id: str
    action: str
    changed_fields_json: dict | list | None
    review_comment: str | None
    reviewed_by: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
