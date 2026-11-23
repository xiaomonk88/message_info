import secrets
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import delete, desc, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.deps import db_session, get_current_user, require_admin
from app.models.grant import Attachment, ModuleGrant, RecordGrant
from app.models.user import User
from app.services.access import get_module_access, visible_module_ids, visible_record_count
from app.models.audit import AuditLog
from app.models.category import Category
from app.models.field import Field
from app.models.module import Module, ModuleField
from app.models.record import Record
from app.schemas.system import (
    AuditList,
    AuditOut,
    AuditSettings,
    AuditSettingsUpdate,
    BackupList,
    BackupSchedule,
    BackupScheduleUpdate,
    ClearAllResult,
    ClearRecordsResult,
    DangerConfirm,
    RestoreBackupIn,
    SftpBackupConfig,
    SftpBackupConfigUpdate,
    SystemInfo,
)
from app.services import audit
from app.services.backup import (
    create_backup,
    create_full_backup,
    delete_all_backups,
    delete_backup,
    get_schedule,
    list_backups,
    restore_backup,
    save_schedule,
    save_uploaded_backup,
)
from app.services.sftp_backup import (
    get_sftp_config,
    save_sftp_config,
    test_sftp_connection,
    upload_file,
)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/info", response_model=SystemInfo)
def info(db: Session = Depends(db_session), user: User = Depends(get_current_user)):
    if not user.is_admin:
        # 成员：只统计自己可见的板块与记录
        modules = db.scalars(select(Module).where(Module.id.in_(visible_module_ids(db, user) or [-1]))).all()
        records = sum(visible_record_count(db, get_module_access(db, user, m)) for m in modules)
        owned = db.scalar(
            select(func.count(Record.id)).where(Record.created_by == user.id, Record.is_deleted == False)  # noqa
        ) or 0
        return SystemInfo(record_total=records, module_total=len(modules), field_total=0, owned_total=owned)
    return SystemInfo(
        record_total=db.scalar(select(func.count(Record.id)).where(Record.is_deleted == False)) or 0,  # noqa
        module_total=db.scalar(select(func.count(Module.id))) or 0,
        field_total=db.scalar(select(func.count(Field.id))) or 0,
        user_total=db.scalar(select(func.count(User.id))) or 0,
    )


@router.get("/audit-logs", response_model=AuditList)
def list_audit(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    entity_type: str | None = None,
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
):
    stmt = select(AuditLog).order_by(desc(AuditLog.id))
    cstmt = select(func.count(AuditLog.id))
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
        cstmt = cstmt.where(AuditLog.entity_type == entity_type)
    total = db.scalar(cstmt) or 0
    rows = db.scalars(stmt.limit(page_size).offset((page - 1) * page_size)).all()
    return AuditList(items=[AuditOut.model_validate(r) for r in rows], total=total)


@router.get("/audit-settings", response_model=AuditSettings)
def get_audit_settings(
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
):
    return AuditSettings(**audit.get_settings(db))


@router.put("/audit-settings", response_model=AuditSettings)
def update_audit_settings(
    payload: AuditSettingsUpdate,
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
):
    return AuditSettings(**audit.save_settings(
        db,
        enabled=payload.enabled,
        max_count=payload.max_count,
        max_days=payload.max_days,
    ))


@router.post("/audit-logs/clear")
def clear_audit_logs(
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
):
    return audit.clear(db)


@router.post("/backup")
def backup(_: User = Depends(require_admin)):
    return create_backup(remote_trigger="manual")


@router.post("/backup/full")
def full_backup(_: User = Depends(require_admin)):
    return create_full_backup(remote_trigger="manual")


@router.get("/backups", response_model=BackupList)
def backups(_: User = Depends(require_admin)):
    return BackupList(items=list_backups())


@router.delete("/backups")
def delete_backups(_: User = Depends(require_admin)):
    return delete_all_backups()


@router.delete("/backup/{filename}")
def delete_backup_api(filename: str, _: User = Depends(require_admin)):
    return delete_backup(filename)


@router.post("/backups/delete")
def delete_backups_post(_: User = Depends(require_admin)):
    return delete_all_backups()


@router.post("/backup/delete")
def delete_backup_post(payload: RestoreBackupIn, _: User = Depends(require_admin)):
    return delete_backup(payload.filename)


@router.post("/backup/restore")
def restore_backup_api(payload: RestoreBackupIn, _: User = Depends(require_admin)):
    return restore_backup(payload.filename)


@router.get("/backup/schedule", response_model=BackupSchedule)
def get_backup_schedule(
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
):
    return BackupSchedule(**get_schedule(db))


@router.put("/backup/schedule", response_model=BackupSchedule)
def update_backup_schedule(
    payload: BackupScheduleUpdate,
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
):
    return BackupSchedule(**save_schedule(db, enabled=payload.enabled, interval_hours=payload.interval_hours))


@router.get("/backup/sftp", response_model=SftpBackupConfig)
def get_sftp_backup_config(
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
):
    return SftpBackupConfig(**get_sftp_config(db))


@router.put("/backup/sftp", response_model=SftpBackupConfig)
def update_sftp_backup_config(
    payload: SftpBackupConfigUpdate,
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
):
    return SftpBackupConfig(**save_sftp_config(db, payload.model_dump()))


@router.post("/backup/sftp/test")
def test_sftp_backup_config(
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
):
    return test_sftp_connection(db)


@router.post("/backup/sftp/sync-latest")
def sync_latest_backup_to_sftp(
    db: Session = Depends(db_session),
    _: User = Depends(require_admin),
):
    items = list_backups()
    if not items:
        raise HTTPException(status_code=404, detail="暂无本地备份文件")
    filename = items[0]["filename"]
    path = settings.backup_dir_path / filename
    return upload_file(db, path)


@router.get("/backup/download/{filename}")
def download_backup(filename: str, _: User = Depends(require_admin)):
    target = (settings.backup_dir_path / filename).resolve()
    if settings.backup_dir_path.resolve() not in target.parents:
        raise HTTPException(status_code=400, detail="非法路径")
    if not target.exists():
        raise HTTPException(status_code=404, detail="备份不存在")
    return FileResponse(target, filename=filename, media_type="application/octet-stream")


@router.post("/backup/upload")
async def upload_backup_api(
    file: UploadFile = File(...),
    restore_now: bool = Query(True),
    user: User = Depends(require_admin),
):
    raw_name = file.filename or ""
    suffix = Path(raw_name).suffix.lower()
    if suffix not in {".db", ".zip"}:
        raise HTTPException(status_code=400, detail="仅支持上传 .zip（完整备份）或 .db（数据库快照）文件")

    max_bytes = 512 * 1024 * 1024  # 512 MB
    backup_dir = settings.backup_dir_path
    temp_path = backup_dir / f".upload_{secrets.token_hex(8)}.tmp"
    total = 0

    try:
        with temp_path.open("wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(status_code=413, detail="备份文件超过 512MB 限制")
                out.write(chunk)
        if total == 0:
            raise HTTPException(status_code=400, detail="上传的备份文件为空")

        result = save_uploaded_backup(raw_name, temp_path, restore_now=restore_now)
    finally:
        await file.close()
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

    try:
        db = SessionLocal()
        try:
            audit.log(
                db,
                action="上传并恢复备份" if restore_now else "上传备份文件",
                entity_type="system",
                summary=f"本地上传备份 {result['filename']} ({total} bytes)" + (" 并已完成恢复" if restore_now else ""),
                actor=user.username,
            )
            db.commit()
        finally:
            db.close()
    except Exception:
        pass

    return result


# ---------- 危险操作 ----------

def _clear_uploads_dir() -> int:
    """清空 uploads 目录下所有文件与子目录，返回删除条目数量。"""
    upload_dir: Path = settings.upload_dir_path
    count = 0
    if not upload_dir.exists():
        return 0
    for item in upload_dir.iterdir():
        try:
            if item.is_dir() and not item.is_symlink():
                shutil.rmtree(item)
            else:
                item.unlink()
            count += 1
        except Exception:
            pass
    return count


@router.post("/danger/clear-records", response_model=ClearRecordsResult)
def clear_all_records(
    payload: DangerConfirm,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """清空所有板块的记录数据 + 上传文件，但保留分类/字段/板块结构。"""
    if payload.confirm != "YES":
        raise HTTPException(status_code=400, detail="请输入 YES 以确认操作")

    record_count = db.scalar(select(func.count(Record.id))) or 0
    db.execute(delete(RecordGrant))
    db.execute(delete(Attachment))
    db.execute(delete(Record))

    uploaded = _clear_uploads_dir()

    audit.log(
        db,
        action="清空记录",
        entity_type="system",
        summary=f"清空全部记录 {record_count} 条 · 删除上传 {uploaded} 项",
        actor=user.username,
    )
    db.commit()

    return ClearRecordsResult(
        deleted_records=int(record_count),
        deleted_uploads=int(uploaded),
    )


@router.post("/danger/clear-all", response_model=ClearAllResult)
def clear_all_data(
    payload: DangerConfirm,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """工厂重置：清空记录、板块、字段、分类、操作日志、上传文件。"""
    if payload.confirm != "YES":
        raise HTTPException(status_code=400, detail="请输入 YES 以确认操作")

    record_count = db.scalar(select(func.count(Record.id))) or 0
    module_count = db.scalar(select(func.count(Module.id))) or 0
    field_count = db.scalar(select(func.count(Field.id))) or 0
    category_count = db.scalar(select(func.count(Category.id))) or 0

    # 按依赖顺序清空（保留用户账号，清空其授权）
    db.execute(delete(RecordGrant))
    db.execute(delete(ModuleGrant))
    db.execute(delete(Attachment))
    db.execute(delete(Record))
    db.execute(delete(ModuleField))
    db.execute(delete(Module))
    db.execute(delete(Field))
    db.execute(delete(Category))
    db.execute(delete(AuditLog))
    db.commit()

    uploaded = _clear_uploads_dir()

    return ClearAllResult(
        deleted_records=int(record_count),
        deleted_modules=int(module_count),
        deleted_fields=int(field_count),
        deleted_categories=int(category_count),
        deleted_uploads=int(uploaded),
    )
