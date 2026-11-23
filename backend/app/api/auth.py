import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import db_session, get_current_user, require_admin
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import ROLE_MEMBER, User
from app.schemas.auth import (
    AuthSettings,
    ChangePasswordRequest,
    ChangeUsernameRequest,
    LoginRequest,
    MeResponse,
    RegisterRequest,
    TokenResponse,
)
from app.services import audit
from app.services.bootstrap import get_allow_register, set_allow_register

router = APIRouter(prefix="/auth", tags=["auth"])

# 用户名：2-32 位，字母 / 数字 / 中文 / _ . -
USERNAME_RE = re.compile(r"^[\w.\-一-龥]{2,32}$")


def validate_username(name: str) -> str:
    name = (name or "").strip()
    if not USERNAME_RE.match(name):
        raise HTTPException(status_code=400, detail="用户名需 2-32 位，可用字母、数字、中文、_ . -")
    return name


def validate_password(pwd: str) -> str:
    if not pwd or len(pwd) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")
    if len(pwd) > 128:
        raise HTTPException(status_code=400, detail="密码过长")
    return pwd


def username_taken(db: Session, name: str, exclude_id: int | None = None) -> bool:
    stmt = select(User.id).where(func.lower(User.username) == name.lower())
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    return db.scalar(stmt) is not None


def _client_ip(req: Request) -> str | None:
    fwd = req.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return req.client.host if req.client else None


def _issue(db: Session, user: User) -> TokenResponse:
    user.last_login_at = datetime.utcnow()
    db.commit()
    return TokenResponse(
        access_token=create_access_token(user.id, user.token_version),
        username=user.username,
        role=user.role,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(db_session)):
    user = db.scalar(select(User).where(func.lower(User.username) == (payload.username or "").strip().lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用，请联系管理员")
    audit.log(db, action="login", entity_type="user", entity_id=user.id, actor=user.username, ip=_client_ip(request))
    return _issue(db, user)


@router.get("/settings", response_model=AuthSettings)
def get_auth_settings(db: Session = Depends(db_session)):
    """公开接口：登录页据此决定是否显示「注册」入口。"""
    return AuthSettings(allow_register=get_allow_register(db))


@router.put("/settings", response_model=AuthSettings)
def update_auth_settings(
    payload: AuthSettings,
    db: Session = Depends(db_session),
    admin: User = Depends(require_admin),
):
    set_allow_register(db, payload.allow_register)
    audit.log(
        db,
        action="update",
        entity_type="system",
        summary=f"{'开启' if payload.allow_register else '关闭'}用户注册",
        actor=admin.username,
    )
    db.commit()
    return AuthSettings(allow_register=get_allow_register(db))


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(db_session)):
    if not get_allow_register(db):
        raise HTTPException(status_code=403, detail="当前未开放注册")
    username = validate_username(payload.username)
    validate_password(payload.password)
    if username_taken(db, username):
        raise HTTPException(status_code=400, detail="用户名已被占用")
    display_name = (payload.display_name or "").strip()[:64] or None
    user = User(
        username=username,
        password_hash=hash_password(payload.password),
        display_name=display_name,
        role=ROLE_MEMBER,
        is_active=True,
    )
    db.add(user)
    db.flush()
    audit.log(db, action="register", entity_type="user", entity_id=user.id, actor=username, ip=_client_ip(request))
    return _issue(db, user)


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    return MeResponse(id=user.id, username=user.username, display_name=user.display_name, role=user.role)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
):
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    validate_password(payload.new_password)
    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1  # 其它设备上的登录同时失效
    audit.log(db, action="change_password", entity_type="user", entity_id=user.id, actor=user.username)
    db.commit()
    return {"ok": True}


@router.post("/change-username")
def change_username(
    payload: ChangeUsernameRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
):
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="密码错误")
    new_username = validate_username(payload.new_username)
    if new_username == user.username:
        raise HTTPException(status_code=400, detail="新用户名与当前相同")
    if username_taken(db, new_username, exclude_id=user.id):
        raise HTTPException(status_code=400, detail="用户名已被占用")
    old = user.username
    user.username = new_username
    user.token_version += 1
    audit.log(
        db, action="change_username", entity_type="user", entity_id=user.id, summary=f"{old} → {new_username}", actor=new_username
    )
    db.commit()
    return {"ok": True, "username": new_username}
