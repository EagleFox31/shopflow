from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    label: str = Field(default="Home", max_length=80)
    recipient_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=6, max_length=40)
    line1: str = Field(min_length=2, max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=2, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    country: str = Field(default="CM", min_length=2, max_length=2)
    postal_code: str | None = Field(default=None, max_length=30)
    is_default: bool = False


class AddressUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=80)
    recipient_name: str | None = Field(default=None, min_length=2, max_length=160)
    phone: str | None = Field(default=None, min_length=6, max_length=40)
    line1: str | None = Field(default=None, min_length=2, max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    postal_code: str | None = Field(default=None, max_length=30)
    is_default: bool | None = None


class AddressRead(BaseModel):
    id: int
    user_id: int
    label: str
    recipient_name: str
    phone: str
    line1: str
    line2: str | None
    city: str
    region: str | None
    country: str
    postal_code: str | None
    is_default: bool

    model_config = ConfigDict(from_attributes=True)
