"""用户管理与授权（仅管理员）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.api.auth import username_taken, validate_password, validate_username
from app.core.deps import db_session, require_admin
from app.core.security import hash_password
from app.models.grant import SCOPE_ALL, SCOPE_OWN, Attachment, ModuleGrant, RecordGrant
from app.models.module import Module
from app.models.record import Record
from app.models.user import ROLE_ADMIN, User
from app.schemas.user import GrantsUpdate, ModuleGrantOut, UserCreate, UserOut, UserUpdate
from app.services import audit

router = APIRouter(prefix="/users", tags=["users"])


def _get_user(db: Session, user_id: int) -> User:
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    return u


def _active_admin_count(db: Session, exclude_id: int | None = None) -> int:
    stmt = select(func.count(User.id)).where(User.role == ROLE_ADMIN, User.is_active == True)  # noqa
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    return db.scalar(stmt) or 0


def _counts(db: Session) -> tuple[dict[int, int], dict[int, int], dict[int, int]]:
    owned = dict(
        db.execute(
            select(Record.created_by, func.count(Record.id))
            .where(Record.is_deleted == False, Record.created_by.is_not(None))  # noqa
            .group_by(Record.created_by)
        ).all()
    )
    grants = dict(db.execute(select(ModuleGrant.user_id, func.count(ModuleGrant.id)).group_by(ModuleGrant.user_id)).all())
    shared = dict(db.execute(select(RecordGrant.user_id, func.count(RecordGrant.id)).group_by(RecordGrant.user_id)).all())
    return owned, grants, shared


def _out(u: User, owned: dict, grants: dict, shared: dict) -> UserOut:
    return UserOut(
        id=u.id,
        username=u.username,
        display_name=u.display_name,
        role=u.role,
        is_active=u.is_active,
        created_at=u.created_at,
        last_login_at=u.last_login_at,
        owned_records=owned.get(u.id, 0),
        module_grants=grants.get(u.id, 0),
        shared_records=shared.get(u.id, 0),
    )


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(db_session), _: User = Depends(require_admin)):
    users = db.scalars(select(User).order_by(User.id)).all()
    owned, grants, shared = _counts(db)
    return [_out(u, owned, grants, shared) for u in users]


@router.post("", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(db_session), admin: User = Depends(require_admin)):
    username = validate_username(payload.username)
    validate_password(payload.password)
    if username_taken(db, username):
        raise HTTPException(status_code=400, detail="用户名已被占用")
    u = User(
        username=username,
        password_hash=hash_password(payload.password),
        display_name=(payload.display_name or "").strip()[:64] or None,
        role=payload.role,
        is_active=True,
    )
    db.add(u)
    db.flush()
    audit.log(db, action="create", entity_type="user", entity_id=u.id, summary=username, actor=admin.username)
    db.commit()
    return _out(u, {}, {}, {})


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin),
):
    u = _get_user(db, user_id)
    data = payload.model_dump(exclude_unset=True)
    revoke = False

    if "role" in data and data["role"] != u.role:
        if u.id == admin.id:
            raise HTTPException(status_code=400, detail="不能修改自己的角色")
        if u.role == ROLE_ADMIN and _active_admin_count(db, exclude_id=u.id) == 0:
            raise HTTPException(status_code=400, detail="至少需要保留一名可用的管理员")
        u.role = data["role"]
        revoke = True

    if "is_active" in data and data["is_active"] != u.is_active:
        if u.id == admin.id:
            raise HTTPException(status_code=400, detail="不能禁用自己")
        if not data["is_active"] and u.role == ROLE_ADMIN and _active_admin_count(db, exclude_id=u.id) == 0:
            raise HTTPException(status_code=400, detail="至少需要保留一名可用的管理员")
        u.is_active = bool(data["is_active"])
        revoke = True

    if "display_name" in data:
        u.display_name = (data["display_name"] or "").strip()[:64] or None

    if data.get("password"):
        validate_password(data["password"])
        u.password_hash = hash_password(data["password"])
        revoke = True

    if revoke:
        u.token_version += 1
    changes = {k: v for k, v in data.items() if k != "password"}
    if data.get("password"):
        changes["password"] = "已重置"
    audit.log(db, action="update", entity_type="user", entity_id=u.id, summary=u.username, changes=changes, actor=admin.username)
    db.commit()
    owned, grants, shared = _counts(db)
    return _out(u, owned, grants, shared)


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(db_session), admin: User = Depends(require_admin)):
    u = _get_user(db, user_id)
    if u.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    if u.role == ROLE_ADMIN and _active_admin_count(db, exclude_id=u.id) == 0:
        raise HTTPException(status_code=400, detail="至少需要保留一名可用的管理员")
    name = u.username
    # 旧库的 records.created_by 由 ALTER 添加、没有外键约束，这里显式处理
    db.execute(update(Record).where(Record.created_by == u.id).values(created_by=None))
    db.execute(update(Attachment).where(Attachment.user_id == u.id).values(user_id=None))
    db.execute(delete(ModuleGrant).where(ModuleGrant.user_id == u.id))
    db.execute(delete(RecordGrant).where(RecordGrant.user_id == u.id))
    db.delete(u)
    audit.log(db, action="delete", entity_type="user", entity_id=user_id, summary=name, actor=admin.username)
    db.commit()
    return {"ok": True}


@router.get("/{user_id}/grants", response_model=list[ModuleGrantOut])
def get_grants(user_id: int, db: Session = Depends(db_session), _: User = Depends(require_admin)):
    _get_user(db, user_id)
    grants = db.scalars(select(ModuleGrant).where(ModuleGrant.user_id == user_id)).all()
    shared = dict(
        db.execute(
            select(Record.module_id, func.count(RecordGrant.id))
            .join(Record, Record.id == RecordGrant.record_id)
            .where(RecordGrant.user_id == user_id)
            .group_by(Record.module_id)
        ).all()
    )
    out = [
        ModuleGrantOut(
            module_id=g.module_id,
            scope=g.scope,
            can_create=g.can_create,
            can_edit=g.can_edit,
            can_delete=g.can_delete,
            shared_records=shared.pop(g.module_id, 0),
        )
        for g in grants
    ]
    out.extend(
        ModuleGrantOut(module_id=mid, granted=False, can_create=False, shared_records=n) for mid, n in shared.items()
    )
    return out


@router.put("/{user_id}/grants", response_model=list[ModuleGrantOut])
def set_grants(
    user_id: int,
    payload: GrantsUpdate,
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin),
):
    u = _get_user(db, user_id)
    if u.role == ROLE_ADMIN:
        raise HTTPException(status_code=400, detail="管理员拥有全部权限，无需授权")
    module_ids = {m for m in db.scalars(select(Module.id)).all()}
    wanted: dict[int, dict] = {}
    for item in payload.items:
        if item.module_id not in module_ids:
            raise HTTPException(status_code=400, detail=f"板块 {item.module_id} 不存在")
        wanted[item.module_id] = item.model_dump()

    existing = {g.module_id: g for g in db.scalars(select(ModuleGrant).where(ModuleGrant.user_id == user_id)).all()}
    for mid, g in existing.items():
        if mid not in wanted:
            db.delete(g)
    for mid, cfg in wanted.items():
        g = existing.get(mid) or ModuleGrant(user_id=user_id, module_id=mid)
        g.scope = SCOPE_ALL if cfg["scope"] == SCOPE_ALL else SCOPE_OWN
        g.can_create = bool(cfg["can_create"])
        g.can_edit = bool(cfg["can_edit"])
        g.can_delete = bool(cfg["can_delete"])
        if mid not in existing:
            db.add(g)
    audit.log(
        db,
        action="update",
        entity_type="grant",
        entity_id=user_id,
        summary=f"{u.username} 的板块授权：{len(wanted)} 个",
        actor=admin.username,
    )
    db.commit()
    return get_grants(user_id, db, admin)
