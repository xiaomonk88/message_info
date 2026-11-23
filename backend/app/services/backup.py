import asyncio
import json
import shutil
import sqlite3
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models.app_config import AppConfig

SCHEDULE_KEY = "backup.schedule"


def _now() -> datetime:
    return datetime.now()


def _safe_backup_path(filename: str) -> Path:
    backup_dir = settings.backup_dir_path.resolve()
    target = (backup_dir / filename).resolve()
    if backup_dir not in target.parents or target.suffix not in {".db", ".zip"}:
        raise HTTPException(status_code=400, detail="非法备份文件")
    return target


def _validate_sqlite_file(path: Path) -> None:
    if not path.exists():
        raise HTTPException(status_code=404, detail="备份文件不存在")
    try:
        conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        result = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=400, detail=f"备份文件不可读取：{exc}") from exc
    if not result or result[0] != "ok":
        raise HTTPException(status_code=400, detail="备份文件完整性检查失败")


def _backup_type(path: Path) -> str:
    return "full" if path.suffix.lower() == ".zip" else "database"


def _sqlite_snapshot(dest: Path) -> None:
    src = settings.db_path
    if not src.exists():
        raise HTTPException(status_code=400, detail="数据库不存在")

    conn = sqlite3.connect(str(src))
    try:
        conn.execute(f"VACUUM INTO '{dest.as_posix()}'")
    except sqlite3.OperationalError:
        shutil.copy2(src, dest)
    finally:
        conn.close()


def _validate_full_backup(path: Path) -> None:
    if not path.exists():
        raise HTTPException(status_code=404, detail="备份文件不存在")
    if not zipfile.is_zipfile(path):
        raise HTTPException(status_code=400, detail="完整备份文件格式不正确")
    try:
        with zipfile.ZipFile(path, "r") as zf:
            bad_file = zf.testzip()
            if bad_file:
                raise HTTPException(status_code=400, detail=f"完整备份文件损坏：{bad_file}")
            names = set(zf.namelist())
            if "db/app.db" not in names:
                raise HTTPException(status_code=400, detail="完整备份缺少 db/app.db")
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="完整备份文件不可读取") from exc


def _safe_zip_member_path(root: Path, member_name: str) -> Path:
    normalized = member_name.replace("\\", "/")
    if normalized.startswith("/") or ".." in Path(normalized).parts:
        raise HTTPException(status_code=400, detail=f"完整备份包含非法路径：{member_name}")
    target = (root / normalized).resolve()
    if root.resolve() not in target.parents and target != root.resolve():
        raise HTTPException(status_code=400, detail=f"完整备份包含越界路径：{member_name}")
    return target


def _remove_sqlite_sidecars(db_path: Path) -> None:
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{db_path}{suffix}")
        if not sidecar.exists():
            continue
        try:
            sidecar.unlink()
        except PermissionError as exc:
            raise HTTPException(
                status_code=409,
                detail="数据库文件正在被其他后端进程占用，请确认只启动一个后端服务后重试",
            ) from exc


def create_backup(prefix: str = "backup", remote_trigger: str | None = None) -> dict[str, Any]:
    backup_dir = settings.backup_dir_path
    name = f"{prefix}_{_now().strftime('%Y%m%d_%H%M%S')}.db"
    dest = backup_dir / name

    _sqlite_snapshot(dest)

    result = {
        "type": "database",
        "path": str(dest.relative_to(settings.data_dir_path)),
        "filename": name,
        "size": dest.stat().st_size,
        "created_at": datetime.fromtimestamp(dest.stat().st_mtime),
    }
    if remote_trigger:
        from app.services.sftp_backup import _load_raw_config, upload_file

        db = SessionLocal()
        try:
            cfg = _load_raw_config(db)
            should_upload = cfg.get("enabled") and (
                (remote_trigger == "manual" and cfg.get("upload_on_manual"))
                or (remote_trigger == "schedule" and cfg.get("upload_on_schedule"))
            )
            if should_upload:
                try:
                    result["remote_sync"] = upload_file(db, dest)
                except HTTPException as exc:
                    result["remote_sync"] = {"status": "failed", "error": exc.detail}
        finally:
            db.close()
    return result


def create_full_backup(prefix: str = "full_backup", remote_trigger: str | None = None) -> dict[str, Any]:
    backup_dir = settings.backup_dir_path
    timestamp = _now().strftime("%Y%m%d_%H%M%S")
    name = f"{prefix}_{timestamp}.zip"
    dest = backup_dir / name
    temp_db = backup_dir / f"{prefix}_{timestamp}.tmp.db"

    _sqlite_snapshot(temp_db)
    try:
        upload_root = settings.upload_dir_path
        manifest = {
            "type": "full",
            "app": settings.PROJECT_NAME,
            "created_at": _now().isoformat(timespec="seconds"),
            "database": "db/app.db",
            "includes_uploads": True,
        }
        with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            zf.write(temp_db, "db/app.db")
            for path in upload_root.rglob("*"):
                if not path.is_file():
                    continue
                zf.write(path, f"uploads/{path.relative_to(upload_root).as_posix()}")
    finally:
        if temp_db.exists():
            temp_db.unlink()

    result = {
        "type": "full",
        "path": str(dest.relative_to(settings.data_dir_path)),
        "filename": name,
        "size": dest.stat().st_size,
        "created_at": datetime.fromtimestamp(dest.stat().st_mtime),
    }
    if remote_trigger:
        from app.services.sftp_backup import _load_raw_config, upload_file

        db = SessionLocal()
        try:
            cfg = _load_raw_config(db)
            should_upload = cfg.get("enabled") and (
                (remote_trigger == "manual" and cfg.get("upload_on_manual"))
                or (remote_trigger == "schedule" and cfg.get("upload_on_schedule"))
            )
            if should_upload:
                try:
                    result["remote_sync"] = upload_file(db, dest)
                except HTTPException as exc:
                    result["remote_sync"] = {"status": "failed", "error": exc.detail}
        finally:
            db.close()
    return result


def list_backups() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for pattern in ("*.db", "*.zip"):
        paths = settings.backup_dir_path.glob(pattern)
        for path in paths:
            if path.name.endswith(".tmp.db"):
                continue
            stat = path.stat()
            items.append(
                {
                    "filename": path.name,
                    "type": _backup_type(path),
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime),
                }
            )
    return sorted(items, key=lambda x: x["created_at"], reverse=True)


def delete_backup(filename: str) -> dict[str, Any]:
    target = _safe_backup_path(filename)
    if not target.exists():
        raise HTTPException(status_code=404, detail="备份文件不存在")
    try:
        target.unlink()
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail="备份文件正在被使用，暂时无法删除") from exc
    return {"filename": filename}


def delete_all_backups() -> dict[str, Any]:
    deleted = 0
    skipped: list[str] = []
    for item in list_backups():
        filename = item["filename"]
        try:
            delete_backup(filename)
            deleted += 1
        except HTTPException as exc:
            if exc.status_code == 409:
                skipped.append(filename)
            else:
                raise
    return {"deleted": deleted, "skipped": skipped}


def restore_backup(filename: str) -> dict[str, Any]:
    source = _safe_backup_path(filename)
    if source.suffix.lower() == ".zip":
        return restore_full_backup(filename)
    _validate_sqlite_file(source)

    db_path = settings.db_path
    engine.dispose()
    try:
        source_conn = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
        target_conn = sqlite3.connect(str(db_path))
        try:
            source_conn.backup(target_conn)
            target_conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            target_conn.close()
            source_conn.close()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=409, detail=f"恢复失败，数据库正在使用或备份不可写入：{exc}") from exc

    from app.services.bootstrap import init_database

    init_database()  # 旧备份可能没有 users 等新表
    return {"filename": filename}


def restore_full_backup(filename: str) -> dict[str, Any]:
    source = _safe_backup_path(filename)
    if source.suffix.lower() != ".zip":
        raise HTTPException(status_code=400, detail="请选择完整备份 zip 文件")
    _validate_full_backup(source)

    db_path = settings.db_path
    upload_root = settings.upload_dir_path.resolve()
    engine.dispose()

    with zipfile.ZipFile(source, "r") as zf:
        temp_db = settings.backup_dir_path / f"restore_{_now().strftime('%Y%m%d_%H%M%S')}.tmp.db"
        try:
            with zf.open("db/app.db", "r") as src_db, temp_db.open("wb") as out_db:
                shutil.copyfileobj(src_db, out_db)
            _validate_sqlite_file(temp_db)

            try:
                source_conn = sqlite3.connect(f"file:{temp_db.as_posix()}?mode=ro", uri=True)
                target_conn = sqlite3.connect(str(db_path))
                try:
                    source_conn.backup(target_conn)
                    target_conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                finally:
                    target_conn.close()
                    source_conn.close()
            except sqlite3.Error as exc:
                raise HTTPException(status_code=409, detail=f"恢复失败，数据库正在使用或备份不可写入：{exc}") from exc

            restored_uploads = 0
            for member in zf.infolist():
                if member.is_dir() or not member.filename.startswith("uploads/"):
                    continue
                relative = member.filename[len("uploads/"):]
                if not relative:
                    continue
                target = _safe_zip_member_path(upload_root, relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member, "r") as src_file, target.open("wb") as out_file:
                    shutil.copyfileobj(src_file, out_file)
                restored_uploads += 1
        finally:
            if temp_db.exists():
                temp_db.unlink()

    from app.services.bootstrap import init_database

    init_database()
    return {"filename": filename, "type": "full", "restored_uploads": restored_uploads}


def get_schedule(db: Session) -> dict[str, Any]:
    row = db.get(AppConfig, SCHEDULE_KEY)
    if not row or not row.value:
        return {"enabled": False, "interval_hours": 24, "last_run_at": None}
    data = json.loads(row.value)
    return {
        "enabled": bool(data.get("enabled", False)),
        "interval_hours": int(data.get("interval_hours", 24)),
        "last_run_at": data.get("last_run_at"),
    }


def save_schedule(db: Session, *, enabled: bool, interval_hours: int) -> dict[str, Any]:
    if interval_hours < 1 or interval_hours > 720:
        raise HTTPException(status_code=400, detail="定时间隔必须在 1 到 720 小时之间")
    current = get_schedule(db)
    current["enabled"] = enabled
    current["interval_hours"] = interval_hours
    row = db.get(AppConfig, SCHEDULE_KEY)
    if not row:
        row = AppConfig(key=SCHEDULE_KEY)
        db.add(row)
    row.value = json.dumps(current, ensure_ascii=False)
    db.commit()
    return current


def mark_schedule_run(db: Session, schedule: dict[str, Any]) -> None:
    schedule["last_run_at"] = _now().isoformat(timespec="seconds")
    row = db.get(AppConfig, SCHEDULE_KEY)
    if not row:
        row = AppConfig(key=SCHEDULE_KEY)
        db.add(row)
    row.value = json.dumps(schedule, ensure_ascii=False)
    db.commit()


async def auto_backup_loop(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            db = SessionLocal()
            try:
                schedule = get_schedule(db)
                if schedule["enabled"]:
                    last_run_at = schedule.get("last_run_at")
                    due = True
                    if last_run_at:
                        last = datetime.fromisoformat(last_run_at)
                        due = _now() - last >= timedelta(hours=schedule["interval_hours"])
                    if due:
                        create_backup(prefix="auto_backup", remote_trigger="schedule")
                        mark_schedule_run(db, schedule)
            finally:
                db.close()
        except Exception:
            pass

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=60)
        except asyncio.TimeoutError:
            continue
