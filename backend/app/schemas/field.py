from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field as PField


# Supported field types
FIELD_TYPES = [
    "text",
    "textarea",
    "number",
    "boolean",
    "date",
    "datetime",
    "select",
    "multiselect",
    "url",
    "email",
    "password",
    "image",
    "file",
    "json",
]


class FieldBase(BaseModel):
    code: str = PField(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    name: str = PField(..., min_length=1, max_length=100)
    type: str
    options: Optional[dict[str, Any]] = None
    is_encrypted: bool = False
    is_searchable: Optional[bool] = None
    enable_summary: Optional[bool] = None
    description: Optional[str] = None


class FieldCreate(FieldBase):
    pass


class FieldUpdate(BaseModel):
    name: Optional[str] = PField(None, min_length=1, max_length=100)
    options: Optional[dict[str, Any]] = None
    is_encrypted: Optional[bool] = None
    is_searchable: Optional[bool] = None
    enable_summary: Optional[bool] = None
    description: Optional[str] = None
    # Note: code and type are not updatable once a field is in use


class FieldOut(FieldBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FieldTypeMeta(BaseModel):
    type: str
    label: str
    description: str
    options_schema: dict[str, Any] = {}
