from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def db_session() -> Generator[Session, None, None]:
    yield from get_db()


def _unauthorized(detail: str = "登录已失效，请重新登录") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(db_session)) -> User:
    """校验 token 并返回当前用户；禁用或 token_version 不匹配的一律视为未登录。"""
    payload = decode_token(token)
    if not payload:
        raise _unauthorized()
    user = db.get(User, payload["user_id"])
    if not user or user.token_version != payload["tv"]:
        raise _unauthorized()
    if not user.is_active:
        raise _unauthorized("账号已被禁用")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user
