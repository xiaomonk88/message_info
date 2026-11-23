from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field as PField


class CategoryBase(BaseModel):
    name: str = PField(..., min_length=1, max_length=100)
    icon: Optional[str] = None
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = PField(None, min_length=1, max_length=100)
    icon: Optional[str] = None
    sort_order: Optional[int] = None


class CategoryOut(CategoryBase):
    id: int
    created_at: datetime
    module_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CategoryReorderItem(BaseModel):
    id: int
    sort_order: int


class CategoryReorderRequest(BaseModel):
    items: list[CategoryReorderItem]
