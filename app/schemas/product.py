from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    category_id: int | None = Field(default=None, ge=1)
    name: str = Field(min_length=2, max_length=180)
    sku: str = Field(min_length=1, max_length=100)
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    stock_quantity: int = Field(default=0, ge=0)
    is_active: bool = True


class ProductUpdate(BaseModel):
    category_id: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=180)
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductRead(BaseModel):
    id: int
    shop_id: int
    category_id: int | None
    name: str
    sku: str
    description: str | None
    price: Decimal
    stock_quantity: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
