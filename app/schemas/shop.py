from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShopCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    currency: str = Field(default="XAF", min_length=3, max_length=3)


class ShopUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=160,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    description: str | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    is_active: bool | None = None


class ShopRead(BaseModel):
    id: int
    owner_id: int
    name: str
    slug: str
    description: str | None
    currency: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShopAdminCreate(BaseModel):
    user_id: int
    can_manage_catalog: bool = True
    can_manage_orders: bool = True
    can_manage_users: bool = False


class ShopAdminRead(BaseModel):
    shop_id: int
    user_id: int
    can_manage_catalog: bool
    can_manage_orders: bool
    can_manage_users: bool

    model_config = ConfigDict(from_attributes=True)
