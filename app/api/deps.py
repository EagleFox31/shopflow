from collections.abc import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenError
from app.db.session import get_db
from app.models.user import User
from app.services import token_service, user_role_service, user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db),
) -> User:
    payload = token_service.decode_token(token, expected_type="access")
    return user_service.get_user(int(payload["sub"]), session)


def require_role(role_name: str) -> Callable:
    def dependency(
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db),
    ) -> User:
        if not user_role_service.has_role(current_user.id, role_name, session):
            raise ForbiddenError(f"Role required: {role_name}")
        return current_user

    return dependency
