from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    shops: Mapped[list["Shop"]] = relationship(back_populates="owner")
    shop_admin_links: Mapped[list["ShopAdmin"]] = relationship(back_populates="user")
    addresses: Mapped[list["Address"]] = relationship(back_populates="user")
    carts: Mapped[list["Cart"]] = relationship(back_populates="user")
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="user")
