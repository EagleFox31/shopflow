from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import OrderStatus


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    address_id: Mapped[int] = mapped_column(ForeignKey("addresses.id"))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=20),
        default=OrderStatus.PENDING,
        index=True,
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="XAF")

    shop: Mapped["Shop"] = relationship(back_populates="orders")
    customer: Mapped["User"] = relationship(back_populates="orders")
    address: Mapped["Address"] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderStatusHistory.id"
    )
    payments: Mapped[list["Payment"]] = relationship(back_populates="order")
    shipment: Mapped["Shipment | None"] = relationship(back_populates="order", uselist=False)
