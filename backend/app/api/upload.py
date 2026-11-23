import mimetypes
import secrets
from datetime import datetime
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import db_session, get_current_user
from app.models.grant import Attachment
from app.models.module import Module
from app.models.record import Record
from app.models.user import User
from app.schemas.upload import UploadResponse
from app.services.access import get_module_access

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024

    today = datetime.now().strftime("%Y%m")
    target_dir = settings.upload_dir_path / today
    target_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "").suffix.lower()
    safe_suffix = suffix if len(suffix) <= 16 and suffix.isascii() else ""
    name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(6)}{safe_suffix}"
    full = target_dir / name

    written = 0
    async with aiofiles.open(full, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                await out.close()
                full.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"文件超过 {settings.MAX_UPLOAD_MB} MB")
            await out.write(chunk)

    rel = f"{today}/{name}"
    db.add(Attachment(path=rel, user_id=user.id))
    db.commit()
    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    return UploadResponse(
        path=rel,
        url=f"{settings.API_V1_PREFIX}/files/{rel}",
        filename=file.filename or name,
        size=written,
        mime_type=mime,
    )


def _can_read_file(db: Session, user: User, rel: str) -> bool:
    """管理员 / 上传者本人 / 能看到引用该文件的某条记录的成员。"""
    if user.is_admin:
        return True
    att = db.scalar(select(Attachment).where(Attachment.path == rel))
    if att and att.user_id == user.id:
        return True
    escaped = rel.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    rows = db.scalars(
        select(Record).where(Record.is_deleted == False, Record.data.like(f"%{escaped}%", escape="\\"))  # noqa
    ).all()
    cache: dict[int, object] = {}
    for r in rows:
        if r.module_id not in cache:
            module = db.get(Module, r.module_id)
            cache[r.module_id] = get_module_access(db, user, module) if module else None
        access = cache[r.module_id]
        if access is not None and access.can_view_module and access.can_view(r):
            return True
    return False


@router.get("/files/{path:path}")
def serve_file(path: str, db: Session = Depends(db_session), user: User = Depends(get_current_user)):
    base = settings.upload_dir_path.resolve()
    target = (base / path).resolve()
    # Prevent path traversal
    if base not in target.parents and target != base:
        raise HTTPException(status_code=400, detail="非法路径")
    rel = target.relative_to(base).as_posix()
    if not _can_read_file(db, user, rel):
        raise HTTPException(status_code=404, detail="文件不存在")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(target)
