from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ShopAdmin(TimestampMixin, Base):
    __tablename__ = "shop_admins"

    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    can_manage_catalog: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_manage_orders: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_manage_users: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    shop: Mapped["Shop"] = relationship(back_populates="admins")
    user: Mapped["User"] = relationship(back_populates="shop_admin_links")
