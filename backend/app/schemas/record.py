from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class RecordCreate(BaseModel):
    data: dict[str, Any]


class RecordUpdate(BaseModel):
    data: dict[str, Any]


class RecordFilter(BaseModel):
    field: str
    op: str
    value: Any = None


class RecordSearch(BaseModel):
    keyword: Optional[str] = None
    filters: list[RecordFilter] = Field(default_factory=list)
    page: int = 1
    page_size: int = 20


class RecordOut(BaseModel):
    id: int
    module_id: int
    data: dict[str, Any]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    owner: Optional[str] = None  # 仅管理员可见
    shared_count: int = 0  # 仅管理员可见：已分配给多少人
    can_edit: bool = True
    can_delete: bool = True

    model_config = ConfigDict(from_attributes=True)


class RecordList(BaseModel):
    items: list[RecordOut]
    total: int
    page: int
    page_size: int


class RecordStats(BaseModel):
    sums: dict[str, float] = Field(default_factory=dict)
