"""JWT 签名密钥与字段加密密钥的解析。

优先使用环境变量（.env / docker-compose）；未配置或仍是示例占位值时，
首次启动自动生成随机密钥并保存在 DATA_DIR/secrets/ 下，之后一直沿用。
这样本地开发和 Docker 部署都不必手动生成密钥，且密钥随数据卷持久化。

注意：data/secrets/encryption_key 一旦丢失，已加密的字段将无法解密。
"""
import logging
import os
import secrets as _secrets
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet

from app.core.config import settings

log = logging.getLogger("uvicorn.error")

# .env.example / 旧版默认值，视同「未配置」
_PLACEHOLDER_PREFIXES = ("please-change-me", "change-me")


def _is_placeholder(value: str | None) -> bool:
    v = (value or "").strip()
    return not v or v.lower().startswith(_PLACEHOLDER_PREFIXES)


def _secret_file(name: str) -> Path:
    d = settings.data_dir_path / "secrets"
    d.mkdir(parents=True, exist_ok=True)
    return d / name


def _load_or_create(name: str, generate) -> str:
    path = _secret_file(name)
    if path.exists():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
    value = generate()
    path.write_text(value, encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    log.warning("未配置 %s，已自动生成并保存到 %s（请随数据目录一起备份）", name.upper(), path)
    return value


@lru_cache
def jwt_secret() -> str:
    if not _is_placeholder(settings.JWT_SECRET):
        return settings.JWT_SECRET.strip()
    return _load_or_create("jwt_secret", lambda: _secrets.token_urlsafe(64))


@lru_cache
def encryption_key() -> bytes:
    configured = settings.ENCRYPTION_KEY
    if not _is_placeholder(configured):
        key = configured.strip().encode()
        try:
            Fernet(key)
        except ValueError as exc:
            # 配了值但格式不对：直接报错，避免悄悄换成别的密钥导致历史数据解不开
            raise RuntimeError(
                "ENCRYPTION_KEY 不是合法的 Fernet 密钥。可用以下命令生成："
                'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            ) from exc
        return key
    return _load_or_create("encryption_key", lambda: Fernet.generate_key().decode()).encode()


def ensure_secrets() -> None:
    """启动时调用：提前解析密钥，配置错误能在启动阶段就暴露出来。"""
    jwt_secret()
    encryption_key()
