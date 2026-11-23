from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

SCOPE_OWN = "own"  # 只能看到自己创建的 + 被分配的记录
SCOPE_ALL = "all"  # 能看到板块内全部记录


class ModuleGrant(Base):
    """成员对某个板块的访问授权。"""

    __tablename__ = "module_grants"
    __table_args__ = (UniqueConstraint("user_id", "module_id", name="uq_module_grant"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scope: Mapped[str] = mapped_column(String(8), default=SCOPE_OWN, nullable=False)
    can_create: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # 以下两项只在 scope=all 时作用于他人的记录；自己创建的记录始终可编辑 / 删除
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class RecordGrant(Base):
    """管理员把某条记录分配（共享）给某个成员。"""

    __tablename__ = "record_grants"
    __table_args__ = (UniqueConstraint("user_id", "record_id", name="uq_record_grant"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    record_id: Mapped[int] = mapped_column(
        ForeignKey("records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Attachment(Base):
    """上传文件的归属，用于下载时校验权限。"""

    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
