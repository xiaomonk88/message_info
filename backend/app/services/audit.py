import json
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.models.app_config import AppConfig
from app.models.audit import AuditLog

AUDIT_ENABLED_KEY = "audit.enabled"
AUDIT_MAX_COUNT_KEY = "audit.max_count"
AUDIT_MAX_DAYS_KEY = "audit.max_days"

DEFAULT_AUDIT_SETTINGS = {
    "enabled": True,
    "max_count": 5000,
    "max_days": 180,
}


def _bool_value(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_value(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def get_settings(db: Session) -> dict[str, Any]:
    enabled = db.get(AppConfig, AUDIT_ENABLED_KEY)
    max_count = db.get(AppConfig, AUDIT_MAX_COUNT_KEY)
    max_days = db.get(AppConfig, AUDIT_MAX_DAYS_KEY)
    return {
        "enabled": _bool_value(enabled.value if enabled else None, DEFAULT_AUDIT_SETTINGS["enabled"]),
        "max_count": max(0, _int_value(max_count.value if max_count else None, DEFAULT_AUDIT_SETTINGS["max_count"])),
        "max_days": max(0, _int_value(max_days.value if max_days else None, DEFAULT_AUDIT_SETTINGS["max_days"])),
    }


def save_settings(db: Session, *, enabled: bool, max_count: int, max_days: int) -> dict[str, Any]:
    values = {
        AUDIT_ENABLED_KEY: "1" if enabled else "0",
        AUDIT_MAX_COUNT_KEY: str(max(0, max_count)),
        AUDIT_MAX_DAYS_KEY: str(max(0, max_days)),
    }
    for key, value in values.items():
        row = db.get(AppConfig, key)
        if row:
            row.value = value
        else:
            db.add(AppConfig(key=key, value=value))
    prune(db, max_count=max(0, max_count), max_days=max(0, max_days))
    db.commit()
    return get_settings(db)


def prune(db: Session, *, max_count: int | None = None, max_days: int | None = None) -> None:
    settings = get_settings(db)
    count_limit = settings["max_count"] if max_count is None else max_count
    days_limit = settings["max_days"] if max_days is None else max_days

    if days_limit > 0:
        cutoff = datetime.utcnow() - timedelta(days=days_limit)
        db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff))

    if count_limit > 0:
        old_ids = db.scalars(
            select(AuditLog.id).order_by(desc(AuditLog.id)).offset(count_limit)
        ).all()
        if old_ids:
            db.execute(delete(AuditLog).where(AuditLog.id.in_(old_ids)))


def clear(db: Session) -> dict[str, int]:
    result = db.execute(delete(AuditLog))
    db.commit()
    return {"deleted": result.rowcount or 0}


def log(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    summary: Optional[str] = None,
    changes: Optional[dict[str, Any]] = None,
    actor: Optional[str] = None,
    ip: Optional[str] = None,
) -> None:
    settings = get_settings(db)
    if not settings["enabled"]:
        return

    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        changes=json.dumps(changes, ensure_ascii=False) if changes else None,
        actor=actor,
        ip=ip,
    )
    db.add(entry)
    db.flush()
    prune(db, max_count=settings["max_count"], max_days=settings["max_days"])
