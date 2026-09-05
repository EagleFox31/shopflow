from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import health_service

router = APIRouter(tags=["health"])


@router.get("/health")
def health(session: Session = Depends(get_db)) -> dict[str, str]:
    return health_service.system_health(session)
