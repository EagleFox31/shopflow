from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PaymentStatus


class PaymentCreate(BaseModel):
    provider: str = Field(default="manual", min_length=2, max_length=80)


class PaymentSuccess(BaseModel):
    reference: str = Field(min_length=2, max_length=160)
    provider_payload: dict | None = None


class PaymentFailure(BaseModel):
    provider_payload: dict | None = None


class PaymentRead(BaseModel):
    id: int
    order_id: int
    provider: str
    reference: str | None
    amount: Decimal
    status: PaymentStatus
    paid_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
