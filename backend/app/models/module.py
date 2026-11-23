from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.field import Field


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_load_images: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    calculated_fields: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    fields: Mapped[list["ModuleField"]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="ModuleField.sort_order",
    )


class ModuleField(Base):
    __tablename__ = "module_fields"
    __table_args__ = (UniqueConstraint("module_id", "field_id", name="uq_module_field"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_id: Mapped[int] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_in_list: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    column_width: Mapped[int | None] = mapped_column(Integer, nullable=True)

    module: Mapped[Module] = relationship(back_populates="fields")
    field: Mapped[Field] = relationship(lazy="joined")
