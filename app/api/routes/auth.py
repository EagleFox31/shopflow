from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import RefreshTokenRequest, TokenPair
from app.schemas.user import UserCreate, UserRead
from app.services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(data: UserCreate, session: Session = Depends(get_db)):
    return user_service.register_user(data, session)


@router.post("/login", response_model=TokenPair)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db),
):
    return auth_service.login(form.username, form.password, session)


@router.post("/refresh", response_model=TokenPair)
def refresh(data: RefreshTokenRequest, session: Session = Depends(get_db)):
    return auth_service.refresh(data.refresh_token, session)
