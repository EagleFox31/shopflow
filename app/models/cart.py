from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import CartStatus


class Cart(TimestampMixin, Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), index=True)
    status: Mapped[CartStatus] = mapped_column(
        Enum(CartStatus, native_enum=False, length=20), default=CartStatus.ACTIVE, index=True
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    user: Mapped["User"] = relationship(back_populates="carts")
    shop: Mapped["Shop"] = relationship(back_populates="carts")
    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )
