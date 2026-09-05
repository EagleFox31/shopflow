from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.role import RoleCreate, RoleRead, UserRoleAssign
from app.services import role_service, user_role_service

router = APIRouter(prefix="/admin", tags=["roles"])


@router.get("/roles", response_model=list[RoleRead])
def list_roles(
    _: User = Depends(require_role("platform_admin")),
    session: Session = Depends(get_db),
):
    return role_service.list_roles(session)


@router.post("/roles", response_model=RoleRead, status_code=201)
def create_role(
    data: RoleCreate,
    _: User = Depends(require_role("platform_admin")),
    session: Session = Depends(get_db),
):
    return role_service.create_role(data, session)


@router.post("/users/{user_id}/roles", status_code=201)
def assign_role(
    user_id: int,
    data: UserRoleAssign,
    _: User = Depends(require_role("platform_admin")),
    session: Session = Depends(get_db),
):
    link = user_role_service.assign_role(user_id, data.role_id, session)
    return {"user_id": link.user_id, "role_id": link.role_id}


@router.delete("/users/{user_id}/roles/{role_id}", status_code=204)
def remove_role(
    user_id: int,
    role_id: int,
    _: User = Depends(require_role("platform_admin")),
    session: Session = Depends(get_db),
):
    user_role_service.remove_role(user_id, role_id, session)
    return Response(status_code=204)
