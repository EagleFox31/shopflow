from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Shop(TimestampMixin, Base):
    __tablename__ = "shops"
    __table_args__ = (UniqueConstraint("owner_id", "slug", name="uq_shop_owner_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="XAF")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="shops")
    admins: Mapped[list["ShopAdmin"]] = relationship(back_populates="shop")
    categories: Mapped[list["Category"]] = relationship(back_populates="shop")
    products: Mapped[list["Product"]] = relationship(back_populates="shop")
    carts: Mapped[list["Cart"]] = relationship(back_populates="shop")
    orders: Mapped[list["Order"]] = relationship(back_populates="shop")
