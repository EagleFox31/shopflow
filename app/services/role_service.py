from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.role import Role
from app.schemas.role import RoleCreate


def create_role(data: RoleCreate, session: Session) -> Role:
    if session.scalar(select(Role).where(Role.name == data.name)):
        raise ConflictError("Role already exists")
    role = Role(**data.model_dump())
    session.add(role)
    session.commit()
    session.refresh(role)
    return role


def get_role(role_id: int, session: Session) -> Role:
    role = session.get(Role, role_id)
    if not role:
        raise NotFoundError("Role not found")
    return role


def list_roles(session: Session) -> list[Role]:
    return list(session.scalars(select(Role).order_by(Role.name)).all())


def update_role(role_id: int, data: RoleCreate, session: Session) -> Role:
    role = get_role(role_id, session)
    role.name = data.name
    role.description = data.description
    session.commit()
    session.refresh(role)
    return role


def delete_role(role_id: int, session: Session) -> None:
    role = get_role(role_id, session)
    if role.user_roles:
        raise ConflictError("Cannot delete a role that is assigned to users")
    session.delete(role)
    session.commit()
