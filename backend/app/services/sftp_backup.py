import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import decrypt_value, encrypt_value, is_encrypted
from app.models.app_config import AppConfig

SFTP_CONFIG_KEY = "backup.sftp"
SECRET_FIELDS = {"password", "private_key", "private_key_passphrase"}

DEFAULT_CONFIG: dict[str, Any] = {
    "enabled": False,
    "host": "",
    "port": 22,
    "username": "",
    "auth_type": "password",
    "password": "",
    "private_key": "",
    "private_key_passphrase": "",
    "remote_dir": "",
    "upload_on_manual": True,
    "upload_on_schedule": True,
    "last_sync_at": None,
    "last_status": None,
    "last_error": None,
    "last_filename": None,
}


def _now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _load_raw_config(db: Session) -> dict[str, Any]:
    row = db.get(AppConfig, SFTP_CONFIG_KEY)
    if not row or not row.value:
        return dict(DEFAULT_CONFIG)
    try:
        data = json.loads(row.value)
    except json.JSONDecodeError:
        data = {}
    return {**DEFAULT_CONFIG, **data}


def _save_raw_config(db: Session, data: dict[str, Any]) -> dict[str, Any]:
    row = db.get(AppConfig, SFTP_CONFIG_KEY)
    if not row:
        row = AppConfig(key=SFTP_CONFIG_KEY)
        db.add(row)
    row.value = json.dumps(data, ensure_ascii=False)
    db.commit()
    return data


def _decrypt_secret(value: str | None) -> str:
    if not value:
        return ""
    return decrypt_value(value) if is_encrypted(value) else value


def _encrypt_secret(value: str | None) -> str:
    if not value:
        return ""
    return value if is_encrypted(value) else encrypt_value(value)


def public_config(data: dict[str, Any]) -> dict[str, Any]:
    cfg = {**DEFAULT_CONFIG, **data}
    return {
        **{k: v for k, v in cfg.items() if k not in SECRET_FIELDS},
        "password": "",
        "private_key": "",
        "private_key_passphrase": "",
        "has_password": bool(cfg.get("password")),
        "has_private_key": bool(cfg.get("private_key")),
        "has_private_key_passphrase": bool(cfg.get("private_key_passphrase")),
    }


def get_sftp_config(db: Session) -> dict[str, Any]:
    return public_config(_load_raw_config(db))


def save_sftp_config(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    current = _load_raw_config(db)
    auth_type = payload.get("auth_type") or "password"
    if auth_type not in {"password", "private_key"}:
        raise HTTPException(status_code=400, detail="认证方式必须是 password 或 private_key")

    data = {
        **current,
        "enabled": bool(payload.get("enabled", False)),
        "host": str(payload.get("host") or "").strip(),
        "port": int(payload.get("port") or 22),
        "username": str(payload.get("username") or "").strip(),
        "auth_type": auth_type,
        "remote_dir": str(payload.get("remote_dir") or "").strip(),
        "upload_on_manual": bool(payload.get("upload_on_manual", True)),
        "upload_on_schedule": bool(payload.get("upload_on_schedule", True)),
    }
    if data["port"] < 1 or data["port"] > 65535:
        raise HTTPException(status_code=400, detail="SFTP 端口必须在 1 到 65535 之间")

    for field in SECRET_FIELDS:
        incoming = payload.get(field)
        if incoming:
            data[field] = _encrypt_secret(str(incoming))
        elif field not in current:
            data[field] = ""

    _save_raw_config(db, data)
    return public_config(data)


def _require_paramiko():
    try:
        import paramiko
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="后端缺少 paramiko 依赖，请重新安装 requirements.txt") from exc
    return paramiko


def _private_key_from_text(paramiko: Any, key_text: str, passphrase: str | None):
    last_error: Exception | None = None
    for key_cls in (
        paramiko.Ed25519Key,
        paramiko.RSAKey,
        paramiko.ECDSAKey,
        paramiko.DSSKey,
    ):
        try:
            return key_cls.from_private_key(io.StringIO(key_text), password=passphrase or None)
        except Exception as exc:
            last_error = exc
    raise HTTPException(status_code=400, detail=f"私钥无法解析：{last_error}") from last_error


def _connect(cfg: dict[str, Any]):
    paramiko = _require_paramiko()
    host = cfg.get("host")
    username = cfg.get("username")
    remote_dir = cfg.get("remote_dir")
    if not host or not username or not remote_dir:
        raise HTTPException(status_code=400, detail="请填写 SFTP 主机、用户名和远程目录")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs: dict[str, Any] = {
        "hostname": host,
        "port": int(cfg.get("port") or 22),
        "username": username,
        "timeout": 15,
        "banner_timeout": 15,
        "auth_timeout": 15,
    }
    if cfg.get("auth_type") == "private_key":
        key_text = _decrypt_secret(cfg.get("private_key"))
        if not key_text:
            raise HTTPException(status_code=400, detail="请填写 SFTP 私钥")
        kwargs["pkey"] = _private_key_from_text(
            paramiko,
            key_text,
            _decrypt_secret(cfg.get("private_key_passphrase")),
        )
    else:
        password = _decrypt_secret(cfg.get("password"))
        if not password:
            raise HTTPException(status_code=400, detail="请填写 SFTP 密码")
        kwargs["password"] = password

    try:
        client.connect(**kwargs)
        return client, client.open_sftp()
    except HTTPException:
        client.close()
        raise
    except Exception as exc:
        client.close()
        raise HTTPException(status_code=400, detail=f"SFTP 连接失败：{exc}") from exc


def _ensure_remote_dir(sftp: Any, remote_dir: str) -> None:
    normalized = remote_dir.replace("\\", "/").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="远程目录不能为空")
    is_absolute = normalized.startswith("/")
    parts = [p for p in normalized.split("/") if p]
    current = "/" if is_absolute else "."
    for part in parts:
        current = f"{current.rstrip('/')}/{part}" if current != "." else part
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


def upload_file(db: Session, local_path: Path) -> dict[str, Any]:
    cfg = _load_raw_config(db)
    if not cfg.get("enabled"):
        return {"status": "skipped", "reason": "disabled"}
    if not local_path.exists():
        raise HTTPException(status_code=404, detail="本地备份文件不存在")

    client = None
    sftp = None
    filename = local_path.name
    try:
        client, sftp = _connect(cfg)
        remote_dir = str(cfg["remote_dir"]).replace("\\", "/").rstrip("/")
        _ensure_remote_dir(sftp, remote_dir)
        remote_path = f"{remote_dir}/{filename}"
        sftp.put(str(local_path), remote_path)
        cfg.update(
            {
                "last_sync_at": _now_text(),
                "last_status": "success",
                "last_error": "",
                "last_filename": filename,
            }
        )
        _save_raw_config(db, cfg)
        return {"status": "success", "filename": filename, "remote_path": remote_path}
    except HTTPException as exc:
        cfg.update(
            {
                "last_sync_at": _now_text(),
                "last_status": "failed",
                "last_error": str(exc.detail),
                "last_filename": filename,
            }
        )
        _save_raw_config(db, cfg)
        raise
    finally:
        if sftp:
            sftp.close()
        if client:
            client.close()


def test_sftp_connection(db: Session) -> dict[str, Any]:
    cfg = _load_raw_config(db)
    client = None
    sftp = None
    try:
        client, sftp = _connect(cfg)
        _ensure_remote_dir(sftp, str(cfg["remote_dir"]))
        return {"ok": True}
    finally:
        if sftp:
            sftp.close()
        if client:
            client.close()
