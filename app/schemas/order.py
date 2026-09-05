from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OrderStatus


class OrderCreate(BaseModel):
    address_id: int = Field(ge=1)


class OrderUpdate(BaseModel):
    address_id: int | None = Field(default=None, ge=1)


class OrderCancel(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


class ShipmentCreate(BaseModel):
    carrier: str = Field(min_length=2, max_length=120)
    tracking_number: str | None = Field(default=None, max_length=160)


class ReturnOrderRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    sku: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderHistoryRead(BaseModel):
    id: int
    from_status: OrderStatus | None
    to_status: OrderStatus
    note: str | None
    changed_by_user_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    shop_id: int
    customer_id: int
    address_id: int
    status: OrderStatus
    subtotal: Decimal
    total_amount: Decimal
    currency: str
    items: list[OrderItemRead] = []
    history: list[OrderHistoryRead] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
