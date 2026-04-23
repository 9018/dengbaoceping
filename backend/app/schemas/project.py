from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampSchema


class ProjectBase(BaseModel):
    code: str | None = Field(default=None, description="项目编码")
    name: str = Field(..., description="项目名称")
    project_type: str = Field(default="等级保护测评", description="项目类型")
    status: str = Field(default="draft", description="项目状态")
    description: str | None = Field(default=None, description="项目说明")
    storage_root: str | None = Field(default=None, description="项目存储根目录")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    project_type: str | None = None
    status: str | None = None
    description: str | None = None
    storage_root: str | None = None


class ProjectRead(ProjectBase, TimestampSchema):
    id: str

    model_config = ConfigDict(from_attributes=True)
