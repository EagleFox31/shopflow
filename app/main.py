from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.exceptions import DomainError
from app import models  # noqa: F401

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Multi-shop commerce backend with a domain service layer. "
        "OpenAPI is the executable API contract."
    ),
)

app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_prefix)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
