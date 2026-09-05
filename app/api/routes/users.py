from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import Message
from app.schemas.user import PasswordChange, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserRead)
def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return user_service.update_user(current_user.id, data, session)


@router.post("/me/change-password", response_model=Message)
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    user_service.change_password(current_user.id, data, session)
    return Message(message="Password updated")
