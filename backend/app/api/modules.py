import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import db_session, get_current_user, require_admin
from app.models.field import Field
from app.models.module import Module, ModuleField
from app.models.record import Record
from app.models.user import User
from app.schemas.field import FieldOut
from app.schemas.module import (
    CalculatedFieldConfig,
    FieldReorderRequest,
    ModuleCreate,
    ModuleFieldConfig,
    ModuleFieldOut,
    ModuleFieldUpdate,
    ModuleAccessOut,
    ModuleListItem,
    ModuleOut,
    ModuleUpdate,
)
from app.services import audit
from app.services.access import ModuleAccess, require_module_view, visible_module_ids, visible_record_count

router = APIRouter(prefix="/modules", tags=["modules"])


def _field_out(f: Field) -> FieldOut:
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


def _mf_out(mf: ModuleField) -> ModuleFieldOut:
    return ModuleFieldOut(
        id=mf.id,
        field_id=mf.field_id,
        sort_order=mf.sort_order,
        is_required=mf.is_required,
        show_in_list=mf.show_in_list,
        column_width=mf.column_width,
        field=_field_out(mf.field),
    )


def _calculated_fields_out(m: Module) -> list[CalculatedFieldConfig]:
    if not m.calculated_fields:
        return []
    try:
        data = json.loads(m.calculated_fields) or []
        return [CalculatedFieldConfig.model_validate(item) for item in data if isinstance(item, dict)]
    except Exception:
        return []


def _access_out(access: ModuleAccess | None) -> ModuleAccessOut:
    if access is None or access.is_admin:
        return ModuleAccessOut()
    g = access.grant
    return ModuleAccessOut(
        is_admin=False,
        scope=g.scope if g else "own",
        can_create=access.can_create,
        can_edit_all=bool(access.scope_all and g and g.can_edit),
        can_delete_all=bool(access.scope_all and g and g.can_delete),
    )


def _module_out(m: Module, record_count: int = 0, access: ModuleAccess | None = None) -> ModuleOut:
    return ModuleOut(
        id=m.id,
        code=m.code,
        name=m.name,
        icon=m.icon,
        description=m.description,
        sort_order=m.sort_order,
        is_enabled=m.is_enabled,
        auto_load_images=m.auto_load_images,
        category_id=m.category_id,
        created_at=m.created_at,
        fields=[_mf_out(mf) for mf in sorted(m.fields, key=lambda x: x.sort_order)],
        calculated_fields=_calculated_fields_out(m),
        record_count=record_count,
        access=_access_out(access),
    )


def _load_module(db: Session, module_id: int) -> Module:
    stmt = (
        select(Module)
        .options(selectinload(Module.fields).selectinload(ModuleField.field))
        .where(Module.id == module_id)
    )
    m = db.scalar(stmt)
    if not m:
        raise HTTPException(status_code=404, detail="板块不存在")
    return m


def _record_count(db: Session, module_id: int) -> int:
    return (
        db.scalar(
            select(func.count(Record.id)).where(
                Record.module_id == module_id, Record.is_deleted == False  # noqa
            )
        )
        or 0
    )


@router.get("", response_model=list[ModuleListItem])
def list_modules(
    category_id: int | None = None,
    enabled_only: bool = False,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    stmt = select(Module).order_by(Module.sort_order, Module.id)
    visible = visible_module_ids(db, user)
    if visible is not None:
        stmt = stmt.where(Module.id.in_(visible or [-1]))
    if category_id is not None:
        stmt = stmt.where(Module.category_id == category_id)
    if enabled_only:
        stmt = stmt.where(Module.is_enabled == True)  # noqa

    modules = db.scalars(stmt).all()
    if visible is not None:
        # 成员：记录数只统计自己可见的
        member_counts = {
            m.id: visible_record_count(db, require_module_view(db, user, m)) for m in modules
        }

    field_counts = dict(
        db.execute(
            select(ModuleField.module_id, func.count(ModuleField.id)).group_by(ModuleField.module_id)
        ).all()
    )
    record_counts = dict(
        db.execute(
            select(Record.module_id, func.count(Record.id))
            .where(Record.is_deleted == False)  # noqa
            .group_by(Record.module_id)
        ).all()
    )

    return [
        ModuleListItem(
            id=m.id,
            code=m.code,
            name=m.name,
            icon=m.icon,
            description=m.description,
            sort_order=m.sort_order,
            is_enabled=m.is_enabled,
            auto_load_images=m.auto_load_images,
            category_id=m.category_id,
            created_at=m.created_at,
            field_count=field_counts.get(m.id, 0),
            record_count=member_counts[m.id] if visible is not None else record_counts.get(m.id, 0),
        )
        for m in modules
    ]


@router.get("/{module_id}", response_model=ModuleOut)
def get_module(
    module_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    m = _load_module(db, module_id)
    access = require_module_view(db, user, m)
    return _module_out(m, visible_record_count(db, access), access)


@router.post("", response_model=ModuleOut)
def create_module(
    payload: ModuleCreate,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    if db.scalar(select(Module).where(Module.code == payload.code)):
        raise HTTPException(status_code=400, detail="板块编码已存在")

    m = Module(
        code=payload.code,
        name=payload.name,
        icon=payload.icon,
        description=payload.description,
        sort_order=payload.sort_order,
        is_enabled=payload.is_enabled,
        auto_load_images=payload.auto_load_images,
        calculated_fields=json.dumps(
            [cf.model_dump() for cf in payload.calculated_fields],
            ensure_ascii=False,
        ) if payload.calculated_fields else None,
        category_id=payload.category_id,
    )
    db.add(m)
    db.flush()

    for fc in payload.fields:
        if not db.get(Field, fc.field_id):
            raise HTTPException(status_code=400, detail=f"字段 {fc.field_id} 不存在")
        db.add(
            ModuleField(
                module_id=m.id,
                field_id=fc.field_id,
                sort_order=fc.sort_order,
                is_required=fc.is_required,
                show_in_list=fc.show_in_list,
                column_width=fc.column_width,
            )
        )
    audit.log(db, action="create", entity_type="module", entity_id=m.id, summary=m.code, actor=user.username)
    db.commit()
    return get_module(m.id, db, user)


def _sync_module_fields(db: Session, m: Module, configs: list[ModuleFieldConfig]) -> None:
    """按传入列表整体同步板块字段：不在列表中的移除，已有的更新，新的添加。"""
    seen: set[int] = set()
    for fc in configs:
        if fc.field_id in seen:
            raise HTTPException(status_code=400, detail=f"字段 {fc.field_id} 重复")
        seen.add(fc.field_id)
        if not db.get(Field, fc.field_id):
            raise HTTPException(status_code=400, detail=f"字段 {fc.field_id} 不存在")

    existing = {mf.field_id: mf for mf in m.fields}
    for field_id, mf in existing.items():
        if field_id not in seen:
            m.fields.remove(mf)  # delete-orphan 级联删除
    for fc in configs:
        mf = existing.get(fc.field_id)
        if mf is None:
            m.fields.append(
                ModuleField(
                    field_id=fc.field_id,
                    sort_order=fc.sort_order,
                    is_required=fc.is_required,
                    show_in_list=fc.show_in_list,
                    column_width=fc.column_width,
                )
            )
        else:
            mf.sort_order = fc.sort_order
            mf.is_required = fc.is_required
            mf.show_in_list = fc.show_in_list
            mf.column_width = fc.column_width
    db.flush()


@router.patch("/{module_id}", response_model=ModuleOut)
def update_module(
    module_id: int,
    payload: ModuleUpdate,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    m = _load_module(db, module_id)
    data = payload.model_dump(exclude_unset=True)
    if "fields" in data:
        field_configs = payload.fields or []
        _sync_module_fields(db, m, field_configs)
        data.pop("fields")
        data["fields"] = [fc.field_id for fc in field_configs]  # 仅用于审计日志
    if "calculated_fields" in data:
        calculated_fields = data.pop("calculated_fields") or []
        m.calculated_fields = json.dumps(calculated_fields, ensure_ascii=False) if calculated_fields else None
    for k, v in data.items():
        if k == "fields":
            continue
        setattr(m, k, v)
    audit.log(db, action="update", entity_type="module", entity_id=m.id, changes=data, actor=user.username)
    db.commit()
    return get_module(module_id, db, user)


@router.delete("/{module_id}")
def delete_module(
    module_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    m = _load_module(db, module_id)
    code = m.code
    db.delete(m)
    audit.log(db, action="delete", entity_type="module", entity_id=module_id, summary=code, actor=user.username)
    db.commit()
    return {"ok": True}


# ---------- Module-Field management ----------


@router.post("/{module_id}/fields", response_model=ModuleFieldOut)
def add_field_to_module(
    module_id: int,
    payload: ModuleFieldConfig,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    m = _load_module(db, module_id)
    if not db.get(Field, payload.field_id):
        raise HTTPException(status_code=404, detail="字段不存在")
    if db.scalar(
        select(ModuleField).where(
            ModuleField.module_id == module_id, ModuleField.field_id == payload.field_id
        )
    ):
        raise HTTPException(status_code=400, detail="字段已存在于该板块")
    mf = ModuleField(
        module_id=module_id,
        field_id=payload.field_id,
        sort_order=payload.sort_order,
        is_required=payload.is_required,
        show_in_list=payload.show_in_list,
        column_width=payload.column_width,
    )
    db.add(mf)
    audit.log(db, action="add_field", entity_type="module", entity_id=module_id, actor=user.username)
    db.commit()
    db.refresh(mf)
    return _mf_out(mf)


@router.patch("/{module_id}/fields/{field_id}", response_model=ModuleFieldOut)
def update_module_field(
    module_id: int,
    field_id: int,
    payload: ModuleFieldUpdate,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    mf = db.scalar(
        select(ModuleField).where(
            ModuleField.module_id == module_id, ModuleField.field_id == field_id
        )
    )
    if not mf:
        raise HTTPException(status_code=404, detail="板块字段不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(mf, k, v)
    audit.log(db, action="update_field", entity_type="module", entity_id=module_id, actor=user.username)
    db.commit()
    db.refresh(mf)
    return _mf_out(mf)


@router.delete("/{module_id}/fields/{field_id}")
def remove_field_from_module(
    module_id: int,
    field_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    mf = db.scalar(
        select(ModuleField).where(
            ModuleField.module_id == module_id, ModuleField.field_id == field_id
        )
    )
    if not mf:
        raise HTTPException(status_code=404, detail="板块字段不存在")
    db.delete(mf)
    audit.log(db, action="remove_field", entity_type="module", entity_id=module_id, actor=user.username)
    db.commit()
    return {"ok": True}


@router.post("/{module_id}/fields/reorder")
def reorder_module_fields(
    module_id: int,
    payload: FieldReorderRequest,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    for item in payload.items:
        mf = db.scalar(
            select(ModuleField).where(
                ModuleField.module_id == module_id, ModuleField.field_id == item.field_id
            )
        )
        if mf:
            mf.sort_order = item.sort_order
    audit.log(db, action="reorder_fields", entity_type="module", entity_id=module_id, actor=user.username)
    db.commit()
    return {"ok": True}
