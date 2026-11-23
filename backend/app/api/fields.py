import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import db_session, get_current_user, require_admin
from app.models.user import User
from app.models.field import Field
from app.models.module import ModuleField
from app.schemas.field import (
    FIELD_TYPES,
    FieldCreate,
    FieldOut,
    FieldTypeMeta,
    FieldUpdate,
)
from app.services import audit

router = APIRouter(prefix="/fields", tags=["fields"])


FIELD_TYPE_META = [
    FieldTypeMeta(type="text", label="文本", description="单行文本", options_schema={"maxLength": "number", "pattern": "string", "placeholder": "string"}),
    FieldTypeMeta(type="textarea", label="多行文本", description="多行文本框", options_schema={"rows": "number", "maxLength": "number"}),
    FieldTypeMeta(type="number", label="数字", description="整数或小数", options_schema={"min": "number", "max": "number", "precision": "number"}),
    FieldTypeMeta(type="boolean", label="开关", description="布尔值", options_schema={}),
    FieldTypeMeta(type="date", label="日期", description="年-月-日", options_schema={}),
    FieldTypeMeta(type="datetime", label="日期时间", description="带时分秒", options_schema={}),
    FieldTypeMeta(type="select", label="单选", description="下拉单选", options_schema={"choices": "array<{value,label}>"}),
    FieldTypeMeta(type="multiselect", label="多选", description="下拉多选", options_schema={"choices": "array<{value,label}>"}),
    FieldTypeMeta(type="url", label="链接", description="URL", options_schema={}),
    FieldTypeMeta(type="email", label="邮箱", description="Email", options_schema={}),
    FieldTypeMeta(type="password", label="密码", description="加密存储 + 列表脱敏", options_schema={}),
    FieldTypeMeta(type="image", label="图片", description="单张图片上传", options_schema={"maxSize": "number(MB)"}),
    FieldTypeMeta(type="file", label="文件", description="任意文件上传", options_schema={"maxSize": "number(MB)"}),
    FieldTypeMeta(type="json", label="JSON", description="结构化数据", options_schema={}),
]

NON_SEARCHABLE_TYPES = {"password", "image", "file", "json"}


def default_searchable(field_type: str) -> bool:
    return field_type not in NON_SEARCHABLE_TYPES


def normalize_searchable(field_type: str, value: bool | None) -> bool:
    if field_type in NON_SEARCHABLE_TYPES:
        return False
    if value is None:
        return default_searchable(field_type)
    return bool(value)


def normalize_summary(field_type: str, value: bool | None) -> bool:
    return field_type == "number" and bool(value)


def _to_out(f: Field) -> FieldOut:
    options = None
    if f.options:
        try:
            options = json.loads(f.options)
        except json.JSONDecodeError:
            options = None
    return FieldOut(
        id=f.id,
        code=f.code,
        name=f.name,
        type=f.type,
        options=options,
        is_encrypted=f.is_encrypted,
        is_searchable=f.is_searchable,
        enable_summary=f.enable_summary,
        description=f.description,
        created_at=f.created_at,
    )


@router.get("/types", response_model=list[FieldTypeMeta])
def list_types(_: User = Depends(require_admin)):
    return FIELD_TYPE_META


@router.get("", response_model=list[FieldOut])
def list_fields(
    type: str | None = None,
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
):
    stmt = select(Field).order_by(Field.id.desc())
    if type:
        stmt = stmt.where(Field.type == type)
    return [_to_out(f) for f in db.scalars(stmt).all()]


@router.get("/{field_id}", response_model=FieldOut)
def get_field(field_id: int, db: Session = Depends(db_session), _: User = Depends(require_admin)):
    f = db.get(Field, field_id)
    if not f:
        raise HTTPException(status_code=404, detail="字段不存在")
    return _to_out(f)


@router.post("", response_model=FieldOut)
def create_field(
    payload: FieldCreate,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    if payload.type not in FIELD_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的字段类型：{payload.type}")
    if db.scalar(select(Field).where(Field.code == payload.code)):
        raise HTTPException(status_code=400, detail="字段编码已存在")

    is_encrypted = payload.is_encrypted or payload.type == "password"
    is_searchable = False if is_encrypted else normalize_searchable(payload.type, payload.is_searchable)
    enable_summary = normalize_summary(payload.type, payload.enable_summary)
    f = Field(
        code=payload.code,
        name=payload.name,
        type=payload.type,
        options=json.dumps(payload.options, ensure_ascii=False) if payload.options else None,
        is_encrypted=is_encrypted,
        is_searchable=is_searchable,
        enable_summary=enable_summary,
        description=payload.description,
    )
    db.add(f)
    db.flush()
    audit.log(db, action="create", entity_type="field", entity_id=f.id, summary=f.code, actor=user.username)
    db.commit()
    db.refresh(f)
    return _to_out(f)


@router.patch("/{field_id}", response_model=FieldOut)
def update_field(
    field_id: int,
    payload: FieldUpdate,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    f = db.get(Field, field_id)
    if not f:
        raise HTTPException(status_code=404, detail="字段不存在")
    data = payload.model_dump(exclude_unset=True)

    if "options" in data:
        opts = data.pop("options")
        f.options = json.dumps(opts, ensure_ascii=False) if opts else None

    if "is_searchable" in data:
        f.is_searchable = normalize_searchable(f.type, data.pop("is_searchable"))

    if "enable_summary" in data:
        f.enable_summary = normalize_summary(f.type, data.pop("enable_summary"))

    for k in ("name", "is_encrypted", "description"):
        if k in data:
            setattr(f, k, data[k])

    if f.type in NON_SEARCHABLE_TYPES or f.is_encrypted:
        f.is_searchable = False
    if f.type != "number":
        f.enable_summary = False

    audit.log(db, action="update", entity_type="field", entity_id=f.id, changes=data, actor=user.username)
    db.commit()
    db.refresh(f)
    return _to_out(f)


@router.delete("/{field_id}")
def delete_field(
    field_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    f = db.get(Field, field_id)
    if not f:
        raise HTTPException(status_code=404, detail="字段不存在")
    in_use = db.scalar(select(func.count(ModuleField.id)).where(ModuleField.field_id == field_id))
    if in_use:
        raise HTTPException(status_code=400, detail=f"字段被 {in_use} 个板块使用，无法删除")
    db.delete(f)
    audit.log(db, action="delete", entity_type="field", entity_id=field_id, summary=f.code, actor=user.username)
    db.commit()
    return {"ok": True}
