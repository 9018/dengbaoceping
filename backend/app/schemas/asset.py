from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampSchema


class AssetBase(BaseModel):
    asset_kind: str = Field(default="test_object", description="资产用途类型")
    category: str = Field(..., description="文件分类标识")
    category_label: str = Field(..., description="文件分类中文名称")
    batch_no: str | None = Field(default=None, description="上传批次号")
    filename: str = Field(..., description="文件名称")
    primary_ip: str | None = Field(default=None, description="主IP地址")
    file_ext: str | None = Field(default=None, description="文件扩展名")
    mime_type: str | None = Field(default=None, description="文件MIME类型")
    relative_path: str = Field(..., description="相对存储路径")
    absolute_path: str | None = Field(default=None, description="绝对存储路径")
    file_size: int | None = Field(default=None, description="文件大小字节数")
    file_sha256: str | None = Field(default=None, description="文件SHA256摘要")
    file_mtime: datetime | None = Field(default=None, description="文件最后修改时间")
    source: str | None = Field(default=None, description="文件来源")
    ingest_status: str = Field(default="pending", description="入库处理状态")


class AssetCreateRequest(AssetBase):
    pass


class AssetCreate(AssetBase):
    project_id: str = Field(..., description="所属项目ID")


class AssetUpdate(BaseModel):
    asset_kind: str | None = None
    category: str | None = None
    category_label: str | None = None
    batch_no: str | None = None
    filename: str | None = None
    primary_ip: str | None = None
    file_ext: str | None = None
    mime_type: str | None = None
    relative_path: str | None = None
    absolute_path: str | None = None
    file_size: int | None = None
    file_sha256: str | None = None
    file_mtime: datetime | None = None
    source: str | None = None
    ingest_status: str | None = None


class AssetRead(AssetBase, TimestampSchema):
    id: str
    project_id: str

    model_config = ConfigDict(from_attributes=True)
