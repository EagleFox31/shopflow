from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole


def assign_role(user_id: int, role_id: int, session: Session) -> UserRole:
    if not session.get(User, user_id):
        raise NotFoundError("User not found")
    if not session.get(Role, role_id):
        raise NotFoundError("Role not found")
    existing = session.get(UserRole, {"user_id": user_id, "role_id": role_id})
    if existing:
        raise ConflictError("Role already assigned")
    link = UserRole(user_id=user_id, role_id=role_id)
    session.add(link)
    session.commit()
    return link


def remove_role(user_id: int, role_id: int, session: Session) -> None:
    link = session.get(UserRole, {"user_id": user_id, "role_id": role_id})
    if not link:
        raise NotFoundError("Role assignment not found")
    session.delete(link)
    session.commit()


def list_user_roles(user_id: int, session: Session) -> list[Role]:
    statement = (
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
        .order_by(Role.name)
    )
    return list(session.scalars(statement).all())


def has_role(user_id: int, role_name: str, session: Session) -> bool:
    statement = (
        select(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id, Role.name == role_name)
    )
    return session.scalar(statement) is not None
