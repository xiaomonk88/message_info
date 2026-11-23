"""Bootstrap helpers: schema upgrades, seed / migrate users on first run."""
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, engine
from app.core.security import hash_password
from app.models.app_config import AppConfig
from app.models.record import Record
from app.models.user import ROLE_ADMIN, User

# 单用户时代的管理员凭据，只在迁移到 users 表时读取一次
ADMIN_USER_KEY = "admin.username"
ADMIN_PASS_KEY = "admin.password_hash"
ALLOW_REGISTER_KEY = "auth.allow_register"

SEARCHABLE_DEFAULT_TYPES = {
    "text",
    "textarea",
    "number",
    "boolean",
    "date",
    "datetime",
    "select",
    "multiselect",
    "url",
    "email",
}


def ensure_schema(db: Session) -> None:
    """Lightweight SQLite schema upgrades for installs without Alembic."""
    cols = db.execute(text("PRAGMA table_info(fields)")).mappings().all()
    if cols and not any(c["name"] == "is_searchable" for c in cols):
        db.execute(text("ALTER TABLE fields ADD COLUMN is_searchable BOOLEAN NOT NULL DEFAULT 1"))
        searchable = ", ".join(f"'{t}'" for t in sorted(SEARCHABLE_DEFAULT_TYPES))
        db.execute(
            text(
                f"UPDATE fields SET is_searchable = CASE WHEN type IN ({searchable}) "
                "AND is_encrypted = 0 THEN 1 ELSE 0 END"
            )
        )
        db.commit()

    cols = db.execute(text("PRAGMA table_info(fields)")).mappings().all()
    if cols and not any(c["name"] == "enable_summary" for c in cols):
        db.execute(text("ALTER TABLE fields ADD COLUMN enable_summary BOOLEAN NOT NULL DEFAULT 0"))
        db.execute(
            text(
                "UPDATE fields SET enable_summary = 1 "
                "WHERE type = 'number' AND (lower(code) IN ('price', 'jiage') OR name LIKE '%价格%')"
            )
        )
        db.commit()

    module_cols = db.execute(text("PRAGMA table_info(modules)")).mappings().all()
    if module_cols and not any(c["name"] == "auto_load_images" for c in module_cols):
        db.execute(text("ALTER TABLE modules ADD COLUMN auto_load_images BOOLEAN NOT NULL DEFAULT 1"))
        db.commit()

    module_cols = db.execute(text("PRAGMA table_info(modules)")).mappings().all()
    if module_cols and not any(c["name"] == "calculated_fields" for c in module_cols):
        db.execute(text("ALTER TABLE modules ADD COLUMN calculated_fields TEXT"))
        db.commit()

    record_cols = db.execute(text("PRAGMA table_info(records)")).mappings().all()
    if record_cols and not any(c["name"] == "created_by" for c in record_cols):
        db.execute(text("ALTER TABLE records ADD COLUMN created_by INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_records_created_by ON records (created_by)"))
        db.commit()


def _legacy_admin_credentials(db: Session) -> tuple[str | None, str | None]:
    user = db.get(AppConfig, ADMIN_USER_KEY)
    pwd = db.get(AppConfig, ADMIN_PASS_KEY)
    return (user.value if user else None, pwd.value if pwd else None)


def seed_users(db: Session) -> None:
    """users 表为空时创建首个管理员：优先沿用旧版单用户凭据，否则取 .env。
    同时把无主的历史记录归到该管理员名下。"""
    if db.scalar(select(User.id).limit(1)) is not None:
        return
    legacy_name, legacy_hash = _legacy_admin_credentials(db)
    admin = User(
        username=legacy_name or settings.ADMIN_USERNAME,
        password_hash=legacy_hash or hash_password(settings.ADMIN_PASSWORD),
        role=ROLE_ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.flush()
    db.execute(update(Record).where(Record.created_by.is_(None)).values(created_by=admin.id))
    db.commit()


def init_database() -> None:
    """建表 + 轻量迁移 + 用户初始化。启动时与恢复备份后都会调用。"""
    from app.core.database import SessionLocal
    import app.models  # noqa: F401  确保所有模型都已注册到 Base.metadata

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_schema(db)
        seed_users(db)
    finally:
        db.close()


def get_allow_register(db: Session) -> bool:
    row = db.get(AppConfig, ALLOW_REGISTER_KEY)
    return bool(row and row.value == "1")


def set_allow_register(db: Session, value: bool) -> None:
    row = db.get(AppConfig, ALLOW_REGISTER_KEY)
    if row:
        row.value = "1" if value else "0"
    else:
        db.add(AppConfig(key=ALLOW_REGISTER_KEY, value="1" if value else "0"))
