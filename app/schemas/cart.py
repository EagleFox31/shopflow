from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CartStatus


class CartItemUpsert(BaseModel):
    product_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=999)


class CartItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class CartRead(BaseModel):
    id: int
    user_id: int
    shop_id: int
    status: CartStatus
    total_amount: Decimal
    items: list[CartItemRead] = []

    model_config = ConfigDict(from_attributes=True)
