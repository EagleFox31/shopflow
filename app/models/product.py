from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("shop_id", "sku", name="uq_product_shop_sku"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(180), index=True)
    sku: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stock_quantity: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    shop: Mapped["Shop"] = relationship(back_populates="products")
    category: Mapped["Category | None"] = relationship(back_populates="products")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="product")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")
