import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import db_session, get_current_user, require_admin
from app.models.grant import RecordGrant
from app.models.module import Module, ModuleField
from app.models.record import Record
from app.models.user import User
from pydantic import BaseModel

from app.schemas.record import RecordCreate, RecordList, RecordOut, RecordSearch, RecordStats, RecordUpdate
from app.schemas.user import RecordAccessEntry, RecordAccessOut, RecordAccessUpdate, RecordAssignRequest
from app.services import audit
from app.services.access import ModuleAccess, require_module_view
from app.services.encryption import decrypt_record_data, encrypt_record_data
from app.services.validator import ValidationError, validate_record_data

router = APIRouter(prefix="/modules/{module_id}/records", tags=["records"])


class RecordIdsIn(BaseModel):
    ids: list[int]


NON_SEARCHABLE_TYPES = {"password", "image", "file", "json"}


def _load_module(db: Session, module_id: int) -> Module:
    m = db.scalar(
        select(Module)
        .options(selectinload(Module.fields).selectinload(ModuleField.field))
        .where(Module.id == module_id)
    )
    if not m:
        raise HTTPException(status_code=404, detail="板块不存在")
    return m


def _to_out(r: Record, module: Module, access: ModuleAccess | None = None, reveal: bool = True) -> RecordOut:
    raw = json.loads(r.data) if r.data else {}
    data = decrypt_record_data(module, raw, reveal=reveal)
    data.update(_calculated_values(module, data))
    return RecordOut(
        id=r.id,
        module_id=r.module_id,
        data=data,
        is_deleted=r.is_deleted,
        created_at=r.created_at,
        updated_at=r.updated_at,
        created_by=r.created_by,
        can_edit=access.can_edit(r) if access else True,
        can_delete=access.can_delete(r) if access else True,
    )


def _decorate(db: Session, outs: list[RecordOut], access: ModuleAccess) -> list[RecordOut]:
    """管理员视图：补充所有者用户名与分配人数。"""
    if not access.is_admin or not outs:
        return outs
    owner_ids = {o.created_by for o in outs if o.created_by}
    names = dict(db.execute(select(User.id, User.username).where(User.id.in_(owner_ids))).all()) if owner_ids else {}
    ids = [o.id for o in outs]
    shared = dict(
        db.execute(
            select(RecordGrant.record_id, func.count(RecordGrant.id))
            .where(RecordGrant.record_id.in_(ids))
            .group_by(RecordGrant.record_id)
        ).all()
    )
    for o in outs:
        o.owner = names.get(o.created_by) if o.created_by else None
        o.shared_count = shared.get(o.id, 0)
    return outs


def _access(db: Session, user: User, module: Module) -> ModuleAccess:
    return require_module_view(db, user, module)


def _get_visible(db: Session, module_id: int, record_id: int, access: ModuleAccess) -> Record:
    r = db.get(Record, record_id)
    if not r or r.module_id != module_id or r.is_deleted or not access.can_view(r):
        raise HTTPException(status_code=404, detail="记录不存在")
    return r


def _client_ip(req: Request) -> str | None:
    if not req:
        return None
    fwd = req.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return req.client.host if req.client else None


def _searchable_fields(module: Module) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for mf in module.fields:
        f = mf.field
        if not f:
            continue
        if f.type in NON_SEARCHABLE_TYPES or f.is_encrypted or not f.is_searchable:
            continue
        fields[f.code] = f
    return fields


def _text_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _module_calculated_fields(module: Module) -> list[dict[str, Any]]:
    if not module.calculated_fields:
        return []
    try:
        data = json.loads(module.calculated_fields) or []
        return [item for item in data if isinstance(item, dict)]
    except Exception:
        return []


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _remaining_value(data: dict[str, Any], cfg: dict[str, Any]) -> tuple[float | None, dict[str, Any] | None]:
    try:
        amount = float(data.get(cfg.get("amount_field")))
    except (TypeError, ValueError):
        return None, None
    start = _parse_datetime(data.get(cfg.get("start_field")))
    end = _parse_datetime(data.get(cfg.get("end_field")))
    if not start or not end or end <= start:
        return None, None

    now = datetime.now()
    total_seconds = max(1.0, (end - start).total_seconds())
    remaining_seconds = (end - now).total_seconds()
    if remaining_seconds <= 0:
        ratio = 0.0
    elif now <= start:
        ratio = 1.0
    else:
        ratio = min(1.0, remaining_seconds / total_seconds)
    precision = int(cfg.get("precision", 2) or 2)
    value = round(amount * ratio, precision)
    meta = {
        "amount": amount,
        "start": start.isoformat(sep=" "),
        "end": end.isoformat(sep=" "),
        "total_days": round(total_seconds / 86400, 2),
        "remaining_days": round(max(0.0, remaining_seconds) / 86400, 2),
        "ratio": round(ratio, 6),
        "value": value,
    }
    return value, meta


def _calculated_values(module: Module, data: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    meta: dict[str, Any] = {}
    for cfg in _module_calculated_fields(module):
        code = cfg.get("code")
        if not code:
            continue
        if cfg.get("type") == "remaining_value_by_date":
            value, detail = _remaining_value(data, cfg)
            if value is not None:
                values[code] = value
                meta[code] = detail
    if meta:
        values["_calculated_meta"] = meta
    return values


def _bool_value(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "是"}
    return bool(value)


def _match_filter(value: Any, op: str, expected: Any, field_type: str) -> bool:
    text = _text_value(value).lower()
    expected_text = _text_value(expected).lower()
    if op == "empty":
        return text == ""
    if op == "not_empty":
        return text != ""
    if op == "contains":
        return expected_text in text
    if op == "not_contains":
        return expected_text not in text
    if op == "eq":
        if field_type == "boolean":
            return _bool_value(value) == _bool_value(expected)
        return text == expected_text
    if op == "neq":
        if field_type == "boolean":
            return _bool_value(value) != _bool_value(expected)
        return text != expected_text
    if op in {"gt", "gte", "lt", "lte"}:
        try:
            left = float(value)
            right = float(expected)
        except (TypeError, ValueError):
            left = text
            right = expected_text
        if op == "gt":
            return left > right
        if op == "gte":
            return left >= right
        if op == "lt":
            return left < right
        if op == "lte":
            return left <= right
    return True


def _record_matches(data: dict[str, Any], searchable: dict[str, Any], payload: RecordSearch) -> bool:
    terms = [t.lower() for t in (payload.keyword or "").split() if t.strip()]
    if terms:
        haystack = " ".join(_text_value(data.get(code)).lower() for code in searchable)
        if not all(term in haystack for term in terms):
            return False
    for flt in payload.filters:
        field = searchable.get(flt.field)
        if not field:
            return False
        if not _match_filter(data.get(flt.field), flt.op, flt.value, field.type):
            return False
    return True


def _search_records(module: Module, payload: RecordSearch, db: Session, access: ModuleAccess) -> RecordList:
    page = max(1, payload.page)
    page_size = min(200, max(1, payload.page_size))
    searchable = _searchable_fields(module)
    rows = db.scalars(
        select(Record)
        .where(Record.module_id == module.id, Record.is_deleted == False, access.record_clause())  # noqa
        .order_by(Record.id.desc())
    ).all()
    matched: list[RecordOut] = []
    for row in rows:
        out = _to_out(row, module, access)
        if _record_matches(out.data, searchable, payload):
            matched.append(out)
    total = len(matched)
    start = (page - 1) * page_size
    items = _decorate(db, matched[start : start + page_size], access)
    return RecordList(items=items, total=total, page=page, page_size=page_size)


def _summary_fields(module: Module) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for mf in module.fields:
        f = mf.field
        if f and f.type == "number" and f.enable_summary:
            fields[f.code] = f
    for cfg in _module_calculated_fields(module):
        if cfg.get("show_in_list", True) and cfg.get("enable_summary", True):
            code = cfg.get("code")
            if code:
                fields[code] = cfg
    return fields


def _stats_records(module: Module, payload: RecordSearch, db: Session, access: ModuleAccess) -> RecordStats:
    searchable = _searchable_fields(module)
    summary_fields = _summary_fields(module)
    sums = {code: 0.0 for code in summary_fields}
    if not sums:
        return RecordStats(sums={})

    rows = db.scalars(
        select(Record)
        .where(Record.module_id == module.id, Record.is_deleted == False, access.record_clause())  # noqa
        .order_by(Record.id.desc())
    ).all()
    for row in rows:
        out = _to_out(row, module, access)
        if not _record_matches(out.data, searchable, payload):
            continue
        for code in summary_fields:
            value = out.data.get(code)
            if value in (None, ""):
                continue
            try:
                sums[code] += float(value)
            except (TypeError, ValueError):
                continue
    return RecordStats(sums={code: round(value, 2) for code, value in sums.items()})


@router.get("", response_model=RecordList)
def list_records(
    module_id: int,
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort: str | None = None,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    module = _load_module(db, module_id)
    access = _access(db, user, module)
    if keyword:
        return _search_records(
            module, RecordSearch(keyword=keyword, filters=[], page=page, page_size=page_size), db, access
        )

    where = (Record.module_id == module_id, Record.is_deleted == False, access.record_clause())  # noqa
    base = select(Record).where(*where)
    count_stmt = select(func.count(Record.id)).where(*where)

    if sort:
        # format: "field_code:asc" or "field_code:desc" — uses json_extract
        try:
            code, direction = (sort.split(":") + ["asc"])[:2]
            expr = func.json_extract(Record.data, f"$.{code}")
            base = base.order_by(expr.desc() if direction == "desc" else expr.asc())
        except Exception:
            base = base.order_by(Record.id.desc())
    else:
        base = base.order_by(Record.id.desc())

    total = db.scalar(count_stmt) or 0
    rows = db.scalars(base.limit(page_size).offset((page - 1) * page_size)).all()
    return RecordList(
        items=_decorate(db, [_to_out(r, module, access) for r in rows], access),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/search", response_model=RecordList)
def search_records(
    module_id: int,
    payload: RecordSearch,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    module = _load_module(db, module_id)
    return _search_records(module, payload, db, _access(db, user, module))


@router.post("/stats", response_model=RecordStats)
def stats_records(
    module_id: int,
    payload: RecordSearch,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    module = _load_module(db, module_id)
    return _stats_records(module, payload, db, _access(db, user, module))


# ---------- 回收站（仅管理员） ----------


@router.get("/trash", response_model=RecordList)
def list_trash(
    module_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin),
):
    module = _load_module(db, module_id)
    access = ModuleAccess(user=admin, module_id=module_id)
    base = (
        select(Record)
        .where(Record.module_id == module_id, Record.is_deleted == True)  # noqa
        .order_by(Record.updated_at.desc())
    )
    total = db.scalar(
        select(func.count(Record.id)).where(
            Record.module_id == module_id, Record.is_deleted == True  # noqa
        )
    ) or 0
    rows = db.scalars(base.limit(page_size).offset((page - 1) * page_size)).all()
    return RecordList(
        items=_decorate(db, [_to_out(r, module, access) for r in rows], access),
        total=total,
        page=page,
        page_size=page_size,
    )


def _purge(db: Session, rows: list[Record], actor: str) -> int:
    deleted = 0
    for r in rows:
        db.execute(delete(RecordGrant).where(RecordGrant.record_id == r.id))
        db.delete(r)
        deleted += 1
        audit.log(db, action="purge", entity_type="record", entity_id=r.id, actor=actor)
    db.commit()
    return deleted


@router.post("/trash/purge")
def purge_records(
    module_id: int,
    payload: RecordIdsIn,
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin),
):
    if not payload.ids:
        return {"deleted": 0}
    rows = db.scalars(
        select(Record).where(
            Record.module_id == module_id,
            Record.is_deleted == True,  # noqa
            Record.id.in_(payload.ids),
        )
    ).all()
    return {"deleted": _purge(db, list(rows), admin.username)}


@router.post("/trash/purge-all")
def purge_all_trash(
    module_id: int,
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin),
):
    rows = db.scalars(
        select(Record).where(
            Record.module_id == module_id,
            Record.is_deleted == True,  # noqa
        )
    ).all()
    return {"deleted": _purge(db, list(rows), admin.username)}


# ---------- 分配 / 转移（仅管理员） ----------


def _existing_user_ids(db: Session, ids: list[int]) -> set[int]:
    if not ids:
        return set()
    return set(db.scalars(select(User.id).where(User.id.in_(ids))).all())


@router.post("/assign")
def assign_records(
    module_id: int,
    payload: RecordAssignRequest,
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin),
):
    """批量把记录分配给用户 / 取消分配 / 转移所有者。"""
    _load_module(db, module_id)
    record_ids = set(
        db.scalars(
            select(Record.id).where(Record.module_id == module_id, Record.id.in_(payload.record_ids or []))
        ).all()
    )
    if not record_ids:
        raise HTTPException(status_code=400, detail="请选择记录")
    user_ids = _existing_user_ids(db, payload.user_ids)
    if not user_ids:
        raise HTTPException(status_code=400, detail="请选择用户")

    if payload.mode == "transfer":
        if len(user_ids) != 1:
            raise HTTPException(status_code=400, detail="转移所有者只能选择一个用户")
        (new_owner,) = user_ids
        for r in db.scalars(select(Record).where(Record.id.in_(record_ids))).all():
            r.created_by = new_owner
        # 新所有者本身已拥有全部权限，不再需要单独分配
        db.execute(delete(RecordGrant).where(RecordGrant.record_id.in_(record_ids), RecordGrant.user_id == new_owner))
        summary = f"转移 {len(record_ids)} 条记录给用户 #{new_owner}"
    elif payload.mode == "unshare":
        db.execute(
            delete(RecordGrant).where(RecordGrant.record_id.in_(record_ids), RecordGrant.user_id.in_(user_ids))
        )
        summary = f"取消 {len(record_ids)} 条记录对 {len(user_ids)} 个用户的分配"
    else:
        owners = dict(db.execute(select(Record.id, Record.created_by).where(Record.id.in_(record_ids))).all())
        existing = {
            (g.user_id, g.record_id): g
            for g in db.scalars(
                select(RecordGrant).where(RecordGrant.record_id.in_(record_ids), RecordGrant.user_id.in_(user_ids))
            ).all()
        }
        for uid in user_ids:
            for rid in record_ids:
                if owners.get(rid) == uid:
                    continue  # 所有者无需分配
                g = existing.get((uid, rid))
                if g:
                    g.can_edit = payload.can_edit
                else:
                    db.add(RecordGrant(user_id=uid, record_id=rid, can_edit=payload.can_edit))
        summary = f"分配 {len(record_ids)} 条记录给 {len(user_ids)} 个用户（{'可编辑' if payload.can_edit else '只读'}）"

    audit.log(db, action="assign", entity_type="record", summary=summary, actor=admin.username)
    db.commit()
    return {"ok": True, "records": len(record_ids), "users": len(user_ids)}


@router.get("/{record_id}/access", response_model=RecordAccessOut)
def get_record_access(
    module_id: int,
    record_id: int,
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
):
    r = db.get(Record, record_id)
    if not r or r.module_id != module_id:
        raise HTTPException(status_code=404, detail="记录不存在")
    owner = db.get(User, r.created_by) if r.created_by else None
    rows = db.execute(
        select(RecordGrant, User).join(User, User.id == RecordGrant.user_id).where(RecordGrant.record_id == record_id)
    ).all()
    return RecordAccessOut(
        owner_id=owner.id if owner else None,
        owner=owner.username if owner else None,
        shared=[
            RecordAccessEntry(user_id=u.id, username=u.username, display_name=u.display_name, can_edit=g.can_edit)
            for g, u in rows
        ],
    )


@router.put("/{record_id}/access", response_model=RecordAccessOut)
def set_record_access(
    module_id: int,
    record_id: int,
    payload: RecordAccessUpdate,
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin),
):
    r = db.get(Record, record_id)
    if not r or r.module_id != module_id:
        raise HTTPException(status_code=404, detail="记录不存在")
    wanted: dict[int, bool] = {}
    for item in payload.shared:
        try:
            wanted[int(item.get("user_id"))] = bool(item.get("can_edit"))
        except (TypeError, ValueError):
            continue
    valid = _existing_user_ids(db, list(wanted))
    wanted = {uid: edit for uid, edit in wanted.items() if uid in valid and uid != r.created_by}

    existing = {g.user_id: g for g in db.scalars(select(RecordGrant).where(RecordGrant.record_id == record_id)).all()}
    for uid, g in existing.items():
        if uid not in wanted:
            db.delete(g)
    for uid, edit in wanted.items():
        g = existing.get(uid)
        if g:
            g.can_edit = edit
        else:
            db.add(RecordGrant(user_id=uid, record_id=record_id, can_edit=edit))
    audit.log(
        db,
        action="assign",
        entity_type="record",
        entity_id=record_id,
        summary=f"分配给 {len(wanted)} 个用户",
        actor=admin.username,
    )
    db.commit()
    return get_record_access(module_id, record_id, db, admin)


# ---------- 单条记录 ----------


@router.get("/{record_id}", response_model=RecordOut)
def get_record(
    module_id: int,
    record_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    module = _load_module(db, module_id)
    access = _access(db, user, module)
    r = _get_visible(db, module_id, record_id, access)
    return _decorate(db, [_to_out(r, module, access)], access)[0]


@router.post("", response_model=RecordOut)
def create_record(
    module_id: int,
    payload: RecordCreate,
    request: Request,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    module = _load_module(db, module_id)
    access = _access(db, user, module)
    if not access.can_create:
        raise HTTPException(status_code=403, detail="没有在该板块新增记录的权限")
    try:
        normalized = validate_record_data(module, payload.data, partial=False)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"validation": e.errors})

    encrypted = encrypt_record_data(module, normalized)
    r = Record(module_id=module_id, data=json.dumps(encrypted, ensure_ascii=False), created_by=user.id)
    db.add(r)
    db.flush()
    audit.log(
        db,
        action="create",
        entity_type="record",
        entity_id=r.id,
        summary=f"module={module.code}",
        actor=user.username,
        ip=_client_ip(request),
    )
    db.commit()
    db.refresh(r)
    return _decorate(db, [_to_out(r, module, access)], access)[0]


@router.patch("/{record_id}", response_model=RecordOut)
def update_record(
    module_id: int,
    record_id: int,
    payload: RecordUpdate,
    request: Request,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    module = _load_module(db, module_id)
    access = _access(db, user, module)
    r = _get_visible(db, module_id, record_id, access)
    if not access.can_edit(r):
        raise HTTPException(status_code=403, detail="没有编辑该记录的权限")

    try:
        normalized = validate_record_data(module, payload.data, partial=True)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"validation": e.errors})

    current = json.loads(r.data) if r.data else {}
    # Replace strategy: keys present in payload override; keys not present keep
    merged = {**current}
    for k, v in normalized.items():
        merged[k] = v
    # Also allow explicit nulls to clear
    for k, v in payload.data.items():
        if v in (None, ""):
            merged.pop(k, None)

    encrypted = encrypt_record_data(module, merged)
    r.data = json.dumps(encrypted, ensure_ascii=False)
    audit.log(
        db,
        action="update",
        entity_type="record",
        entity_id=r.id,
        summary=f"module={module.code}",
        actor=user.username,
        ip=_client_ip(request),
    )
    db.commit()
    db.refresh(r)
    return _decorate(db, [_to_out(r, module, access)], access)[0]


@router.delete("/{record_id}")
def delete_record(
    module_id: int,
    record_id: int,
    request: Request,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    module = _load_module(db, module_id)
    access = _access(db, user, module)
    r = _get_visible(db, module_id, record_id, access)
    if not access.can_delete(r):
        raise HTTPException(status_code=403, detail="没有删除该记录的权限")
    r.is_deleted = True
    audit.log(
        db,
        action="delete",
        entity_type="record",
        entity_id=record_id,
        actor=user.username,
        ip=_client_ip(request),
    )
    db.commit()
    return {"ok": True}


@router.post("/{record_id}/restore")
def restore_record(
    module_id: int,
    record_id: int,
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin),
):
    r = db.get(Record, record_id)
    if not r or r.module_id != module_id:
        raise HTTPException(status_code=404, detail="记录不存在")
    r.is_deleted = False
    audit.log(db, action="restore", entity_type="record", entity_id=record_id, actor=admin.username)
    db.commit()
    return {"ok": True}


@router.delete("/{record_id}/purge")
def purge_record(
    module_id: int,
    record_id: int,
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin),
):
    r = db.get(Record, record_id)
    if not r or r.module_id != module_id:
        raise HTTPException(status_code=404, detail="记录不存在")
    _purge(db, [r], admin.username)
    return {"ok": True}
