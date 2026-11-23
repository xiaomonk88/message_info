from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AuditOut(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[int]
    summary: Optional[str]
    actor: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditList(BaseModel):
    items: list[AuditOut]
    total: int


class AuditSettings(BaseModel):
    enabled: bool = True
    max_count: int = 5000
    max_days: int = 180


class AuditSettingsUpdate(BaseModel):
    enabled: bool
    max_count: int = Field(ge=0, le=1000000)
    max_days: int = Field(ge=0, le=36500)


class SystemInfo(BaseModel):
    version: str = "0.1.0"
    name: str = "message_info"
    record_total: int = 0
    module_total: int = 0
    field_total: int = 0
    user_total: int = 0
    owned_total: int = 0  # 成员：自己创建的记录数


class BackupFile(BaseModel):
    filename: str
    type: str = "database"
    size: int
    created_at: datetime


class BackupList(BaseModel):
    items: list[BackupFile]


class BackupSchedule(BaseModel):
    enabled: bool = False
    interval_hours: int = 24
    last_run_at: Optional[str] = None


class BackupScheduleUpdate(BaseModel):
    enabled: bool
    interval_hours: int


class RestoreBackupIn(BaseModel):
    filename: str


class SftpBackupConfig(BaseModel):
    enabled: bool = False
    host: str = ""
    port: int = 22
    username: str = ""
    auth_type: str = "password"
    password: str = ""
    private_key: str = ""
    private_key_passphrase: str = ""
    remote_dir: str = ""
    upload_on_manual: bool = True
    upload_on_schedule: bool = True
    has_password: bool = False
    has_private_key: bool = False
    has_private_key_passphrase: bool = False
    last_sync_at: Optional[str] = None
    last_status: Optional[str] = None
    last_error: Optional[str] = None
    last_filename: Optional[str] = None


class SftpBackupConfigUpdate(BaseModel):
    enabled: bool = False
    host: str = ""
    port: int = 22
    username: str = ""
    auth_type: str = "password"
    password: str = ""
    private_key: str = ""
    private_key_passphrase: str = ""
    remote_dir: str = ""
    upload_on_manual: bool = True
    upload_on_schedule: bool = True


class DangerConfirm(BaseModel):
    confirm: str  # 必须等于 "YES"


class ClearRecordsResult(BaseModel):
    deleted_records: int
    deleted_uploads: int


class ClearAllResult(BaseModel):
    deleted_records: int
    deleted_modules: int
    deleted_fields: int
    deleted_categories: int
    deleted_uploads: int
