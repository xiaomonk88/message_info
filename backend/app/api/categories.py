from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import db_session, get_current_user, require_admin
from app.models.user import User
from app.services.access import visible_module_ids
from app.models.category import Category
from app.models.module import Module
from app.schemas.category import (
    CategoryCreate,
    CategoryOut,
    CategoryReorderRequest,
    CategoryUpdate,
)
from app.services import audit

router = APIRouter(prefix="/categories", tags=["categories"])


def _to_out(c: Category, module_count: int = 0) -> CategoryOut:
    return CategoryOut(
        id=c.id,
        name=c.name,
        icon=c.icon,
        sort_order=c.sort_order,
        created_at=c.created_at,
        module_count=module_count,
    )


@router.get("", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(db_session), user: User = Depends(get_current_user)
):
    visible = visible_module_ids(db, user)
    join_cond = Module.category_id == Category.id
    if visible is not None:
        join_cond = join_cond & Module.id.in_(visible or [-1])
    rows = db.execute(
        select(Category, func.count(Module.id))
        .outerjoin(Module, join_cond)
        .group_by(Category.id)
        .order_by(Category.sort_order, Category.id)
    ).all()
    # 成员只看到包含其可见板块的分类
    return [_to_out(c, count or 0) for c, count in rows if visible is None or count]


@router.post("", response_model=CategoryOut)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    existing = db.scalar(select(Category).where(Category.name == payload.name))
    if existing:
        raise HTTPException(status_code=400, detail="分类名称已存在")
    c = Category(**payload.model_dump())
    db.add(c)
    db.flush()
    audit.log(db, action="create", entity_type="category", entity_id=c.id, summary=c.name, actor=user.username)
    db.commit()
    db.refresh(c)
    return _to_out(c, 0)


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    c = db.get(Category, category_id)
    if not c:
        raise HTTPException(status_code=404, detail="分类不存在")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        dup = db.scalar(
            select(Category).where(Category.name == data["name"], Category.id != category_id)
        )
        if dup:
            raise HTTPException(status_code=400, detail="分类名称已存在")
    for k, v in data.items():
        setattr(c, k, v)
    audit.log(db, action="update", entity_type="category", entity_id=c.id, changes=data, actor=user.username)
    db.commit()
    db.refresh(c)
    count = db.scalar(select(func.count(Module.id)).where(Module.category_id == c.id)) or 0
    return _to_out(c, count)


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    c = db.get(Category, category_id)
    if not c:
        raise HTTPException(status_code=404, detail="分类不存在")
    count = db.scalar(select(func.count(Module.id)).where(Module.category_id == c.id)) or 0
    if count > 0:
        raise HTTPException(status_code=400, detail=f"分类下还有 {count} 个板块，无法删除")
    db.delete(c)
    audit.log(db, action="delete", entity_type="category", entity_id=category_id, summary=c.name, actor=user.username)
    db.commit()
    return {"ok": True}


@router.post("/reorder")
def reorder_categories(
    payload: CategoryReorderRequest,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    for item in payload.items:
        c = db.get(Category, item.id)
        if c:
            c.sort_order = item.sort_order
    audit.log(db, action="reorder", entity_type="category", actor=user.username)
    db.commit()
    return {"ok": True}
