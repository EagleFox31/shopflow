from fastapi import FastAPI

from app.api.routes import categories, health, products
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

app.include_router(health.router)
app.include_router(categories.router)
app.include_router(products.router)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {"message": "ShopFlow API"}
