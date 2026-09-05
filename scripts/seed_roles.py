from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.role import Role

DEFAULT_ROLES = {
    "platform_admin": "Global ShopFlow administrator",
    "support": "Platform support role",
}


def main() -> None:
    with SessionLocal() as session:
        for name, description in DEFAULT_ROLES.items():
            if not session.scalar(select(Role).where(Role.name == name)):
                session.add(Role(name=name, description=description))
        session.commit()
    print("Default roles seeded.")


if __name__ == "__main__":
    main()
