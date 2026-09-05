from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=140,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    description: str | None = None


class CategoryRead(BaseModel):
    id: int
    shop_id: int
    name: str
    slug: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)
