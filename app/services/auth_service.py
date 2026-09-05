from sqlalchemy.orm import Session

from app.schemas.auth import TokenPair
from app.services import token_service, user_service


def login(email: str, password: str, session: Session) -> TokenPair:
    user = user_service.authenticate(email, password, session)
    return TokenPair(
        access_token=token_service.create_access_token(user.id),
        refresh_token=token_service.create_refresh_token(user.id),
    )


def refresh(refresh_token: str, session: Session) -> TokenPair:
    payload = token_service.decode_token(refresh_token, expected_type="refresh")
    user = user_service.get_user(int(payload["sub"]), session)
    return TokenPair(
        access_token=token_service.create_access_token(user.id),
        refresh_token=token_service.create_refresh_token(user.id),
    )
