from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field as PField

from app.schemas.field import FieldOut


class ModuleFieldConfig(BaseModel):
    field_id: int
    sort_order: int = 0
    is_required: bool = False
    show_in_list: bool = True
    column_width: Optional[int] = None


class ModuleFieldOut(ModuleFieldConfig):
    id: int
    field: FieldOut

    model_config = ConfigDict(from_attributes=True)


class CalculatedFieldConfig(BaseModel):
    code: str = PField(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    name: str = PField(..., min_length=1, max_length=100)
    type: str = "remaining_value_by_date"
    amount_field: str
    start_field: str
    end_field: str
    precision: int = 2
    sort_order: float = 0
    show_in_list: bool = True
    enable_summary: bool = True


class ModuleBase(BaseModel):
    code: str = PField(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    name: str = PField(..., min_length=1, max_length=100)
    icon: Optional[str] = None
    description: Optional[str] = None
    sort_order: int = 0
    is_enabled: bool = True
    auto_load_images: bool = True
    category_id: Optional[int] = None


class ModuleCreate(ModuleBase):
    fields: list[ModuleFieldConfig] = []
    calculated_fields: list[CalculatedFieldConfig] = []
    copy_records_from_id: Optional[int] = None


class ModuleUpdate(BaseModel):
    name: Optional[str] = PField(None, min_length=1, max_length=100)
    icon: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_enabled: Optional[bool] = None
    auto_load_images: Optional[bool] = None
    category_id: Optional[int] = None
    # 传入时整体同步板块字段：新增 / 移除 / 排序 / 必填 / 列表展示 / 列宽
    fields: Optional[list[ModuleFieldConfig]] = None
    calculated_fields: Optional[list[CalculatedFieldConfig]] = None


class ModuleAccessOut(BaseModel):
    """当前用户在该板块下的能力，前端据此显示 / 隐藏按钮。"""

    is_admin: bool = True
    scope: str = "all"
    can_create: bool = True
    can_edit_all: bool = True
    can_delete_all: bool = True


class ModuleOut(ModuleBase):
    id: int
    created_at: datetime
    fields: list[ModuleFieldOut] = []
    calculated_fields: list[CalculatedFieldConfig] = []
    record_count: int = 0
    access: ModuleAccessOut = ModuleAccessOut()

    model_config = ConfigDict(from_attributes=True)


class ModuleListItem(ModuleBase):
    id: int
    created_at: datetime
    record_count: int = 0
    field_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ModuleFieldUpdate(BaseModel):
    sort_order: Optional[int] = None
    is_required: Optional[bool] = None
    show_in_list: Optional[bool] = None
    column_width: Optional[int] = None


class FieldReorderItem(BaseModel):
    field_id: int
    sort_order: int


class FieldReorderRequest(BaseModel):
    items: list[FieldReorderItem]
