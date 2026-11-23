from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt

from app.core.config import settings
from app.core.secrets import encryption_key, jwt_secret


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (TypeError, ValueError):
        return False


def create_access_token(user_id: int, token_version: int, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "tv": token_version, "exp": expire}
    return jwt.encode(payload, jwt_secret(), algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """返回 {"user_id": int, "tv": int}；无效 / 过期 / 旧格式 token 返回 None。"""
    try:
        data = jwt.decode(token, jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
    sub, tv = data.get("sub"), data.get("tv")
    if not isinstance(sub, str) or not sub.isdigit() or not isinstance(tv, int):
        return None
    return {"user_id": int(sub), "tv": tv}


# Fernet for encrypting sensitive field values
_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(encryption_key())
    return _fernet


ENC_PREFIX = "enc::"


def encrypt_value(plain: str) -> str:
    if plain is None:
        return plain
    token = _get_fernet().encrypt(plain.encode("utf-8")).decode("utf-8")
    return f"{ENC_PREFIX}{token}"


def decrypt_value(value: str) -> str:
    if not isinstance(value, str) or not value.startswith(ENC_PREFIX):
        return value
    try:
        token = value[len(ENC_PREFIX) :]
        return _get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return value


def is_encrypted(value: object) -> bool:
    return isinstance(value, str) and value.startswith(ENC_PREFIX)
