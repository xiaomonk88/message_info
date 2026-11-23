from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Project
    PROJECT_NAME: str = "message_info"
    API_V1_PREFIX: str = "/api/v1"

    # Paths (overridden by env in Docker)
    DATA_DIR: str = str(Path(__file__).resolve().parents[3] / "data")
    DATABASE_URL: Optional[str] = None
    UPLOAD_DIR: Optional[str] = None
    BACKUP_DIR: Optional[str] = None
    STATIC_DIR: Optional[str] = None

    # Auth
    # 留空 / 占位值时自动生成并保存到 DATA_DIR/secrets/（见 app/core/secrets.py）
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Initial admin (used on first start to seed the user)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    # Encryption (Fernet key, base64 url-safe 32 bytes)
    ENCRYPTION_KEY: str = ""

    # Upload
    MAX_UPLOAD_MB: int = 50

    # Misc
    TZ: str = "Asia/Shanghai"

    @property
    def data_dir_path(self) -> Path:
        p = Path(self.DATA_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def db_path(self) -> Path:
        if self.DATABASE_URL and self.DATABASE_URL.startswith("sqlite:///"):
            p = Path(self.DATABASE_URL.replace("sqlite:///", "", 1))
        else:
            p = self.data_dir_path / "db" / "app.db"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def db_url(self) -> str:
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("sqlite:///"):
                self.db_path
            return self.DATABASE_URL
        # SQLite file under data/db
        return f"sqlite:///{self.db_path.as_posix()}"

    @property
    def upload_dir_path(self) -> Path:
        p = Path(self.UPLOAD_DIR) if self.UPLOAD_DIR else self.data_dir_path / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def backup_dir_path(self) -> Path:
        p = Path(self.BACKUP_DIR) if self.BACKUP_DIR else self.data_dir_path / "backups"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def static_dir_path(self) -> Optional[Path]:
        if self.STATIC_DIR:
            p = Path(self.STATIC_DIR)
            return p if p.exists() else None
        # Fallback: project_root/backend/static (used when frontend dist is copied in Docker)
        candidate = Path(__file__).resolve().parents[2] / "static"
        return candidate if candidate.exists() else None


settings = Settings()
