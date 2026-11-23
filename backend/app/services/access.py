"""成员权限计算。

规则（管理员不受限制）：
- 板块可见：板块已启用，且有板块授权或至少一条被分配的记录。
- 记录可见：自己创建的 / 被分配的 / 板块授权范围为「全部记录」。
- 记录可编辑：自己创建的 / 分配时给了编辑权 / 范围为全部且授权允许编辑。
- 记录可删除：自己创建的 / 范围为全部且授权允许删除。
- 新增记录：需要板块授权且允许新增。
"""
from dataclasses import dataclass, field

from fastapi import HTTPException
from sqlalchemy import ColumnElement, func, or_, select, true
from sqlalchemy.orm import Session

from app.models.grant import SCOPE_ALL, ModuleGrant, RecordGrant
from app.models.module import Module
from app.models.record import Record
from app.models.user import User


@dataclass
class ModuleAccess:
    user: User
    module_id: int
    grant: ModuleGrant | None = None
    # record_id -> 是否可编辑
    shared: dict[int, bool] = field(default_factory=dict)

    @property
    def is_admin(self) -> bool:
        return self.user.is_admin

    @property
    def scope_all(self) -> bool:
        return self.is_admin or (self.grant is not None and self.grant.scope == SCOPE_ALL)

    @property
    def can_view_module(self) -> bool:
        return self.is_admin or self.grant is not None or bool(self.shared)

    @property
    def can_create(self) -> bool:
        return self.is_admin or (self.grant is not None and self.grant.can_create)

    def record_clause(self) -> ColumnElement[bool]:
        """可见记录的 SQL 条件（与 module_id / is_deleted 条件组合使用）。"""
        if self.scope_all:
            return true()
        conds = [Record.created_by == self.user.id]
        if self.shared:
            conds.append(Record.id.in_(list(self.shared)))
        return or_(*conds)

    def _owns(self, r: Record) -> bool:
        return r.created_by is not None and r.created_by == self.user.id

    def can_view(self, r: Record) -> bool:
        return self.scope_all or self._owns(r) or r.id in self.shared

    def can_edit(self, r: Record) -> bool:
        if self.is_admin or self._owns(r) or self.shared.get(r.id):
            return True
        return self.scope_all and bool(self.grant and self.grant.can_edit)

    def can_delete(self, r: Record) -> bool:
        if self.is_admin or self._owns(r):
            return True
        return self.scope_all and bool(self.grant and self.grant.can_delete)


def get_module_access(db: Session, user: User, module: Module) -> ModuleAccess:
    access = ModuleAccess(user=user, module_id=module.id)
    if user.is_admin:
        return access
    if not module.is_enabled:
        return access
    access.grant = db.scalar(
        select(ModuleGrant).where(ModuleGrant.user_id == user.id, ModuleGrant.module_id == module.id)
    )
    rows = db.execute(
        select(RecordGrant.record_id, RecordGrant.can_edit)
        .join(Record, Record.id == RecordGrant.record_id)
        .where(RecordGrant.user_id == user.id, Record.module_id == module.id)
    ).all()
    access.shared = {rid: bool(edit) for rid, edit in rows}
    return access


def require_module_view(db: Session, user: User, module: Module) -> ModuleAccess:
    access = get_module_access(db, user, module)
    if not access.can_view_module:
        # 对无权限的成员隐藏板块是否存在
        raise HTTPException(status_code=404, detail="板块不存在")
    return access


def visible_module_ids(db: Session, user: User) -> set[int] | None:
    """成员可见的板块 id；管理员返回 None 表示不限制。"""
    if user.is_admin:
        return None
    granted = set(db.scalars(select(ModuleGrant.module_id).where(ModuleGrant.user_id == user.id)).all())
    shared = set(
        db.scalars(
            select(Record.module_id)
            .join(RecordGrant, RecordGrant.record_id == Record.id)
            .where(RecordGrant.user_id == user.id)
            .distinct()
        ).all()
    )
    ids = granted | shared
    if not ids:
        return set()
    enabled = set(
        db.scalars(select(Module.id).where(Module.id.in_(ids), Module.is_enabled == True)).all()  # noqa
    )
    return enabled


def visible_record_count(db: Session, access: ModuleAccess) -> int:
    return (
        db.scalar(
            select(func.count(Record.id)).where(
                Record.module_id == access.module_id,
                Record.is_deleted == False,  # noqa
                access.record_clause(),
            )
        )
        or 0
    )
