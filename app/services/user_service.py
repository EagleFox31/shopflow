from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import PasswordChange, UserCreate, UserUpdate


def get_user(user_id: int, session: Session) -> User:
    user = session.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")
    return user


def get_user_by_email(email: str, session: Session) -> User | None:
    return session.scalar(select(User).where(User.email == email.lower()))


def register_user(data: UserCreate, session: Session) -> User:
    if get_user_by_email(data.email, session):
        raise ConflictError("Email already registered")
    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user(user_id: int, data: UserUpdate, session: Session) -> User:
    user = get_user(user_id, session)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    session.commit()
    session.refresh(user)
    return user


def change_password(user_id: int, data: PasswordChange, session: Session) -> User:
    user = get_user(user_id, session)
    if not verify_password(data.current_password, user.hashed_password):
        raise UnauthorizedError("Current password is incorrect")
    user.hashed_password = hash_password(data.new_password)
    session.commit()
    return user


def authenticate(email: str, password: str, session: Session) -> User:
    user = get_user_by_email(email, session)
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Invalid credentials")
    if not user.is_active:
        raise UnauthorizedError("Inactive account")
    return user
