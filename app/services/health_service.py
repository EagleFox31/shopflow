from sqlalchemy import text
from sqlalchemy.orm import Session


def database_health(session: Session) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"database": "ok"}


def system_health(session: Session) -> dict[str, str]:
    health = {"status": "ok"}
    health.update(database_health(session))
    return health
