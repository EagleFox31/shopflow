from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.shop_admin import ShopAdmin
from app.models.user import User
from app.schemas.shop import ShopAdminCreate
from app.services import shop_service


def add_admin(
    shop_id: int,
    actor_id: int,
    data: ShopAdminCreate,
    session: Session,
) -> ShopAdmin:
    shop_service.assert_shop_access(shop_id, actor_id, session, owner_only=True)
    if not session.get(User, data.user_id):
        raise NotFoundError("User not found")
    existing = session.get(ShopAdmin, {"shop_id": shop_id, "user_id": data.user_id})
    if existing:
        raise ConflictError("User is already an admin of this shop")
    admin = ShopAdmin(shop_id=shop_id, **data.model_dump())
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin


def remove_admin(shop_id: int, actor_id: int, user_id: int, session: Session) -> None:
    shop_service.assert_shop_access(shop_id, actor_id, session, owner_only=True)
    admin = session.get(ShopAdmin, {"shop_id": shop_id, "user_id": user_id})
    if not admin:
        raise NotFoundError("Shop admin not found")
    session.delete(admin)
    session.commit()


def list_admins(shop_id: int, actor_id: int, session: Session) -> list[ShopAdmin]:
    shop_service.assert_shop_access(shop_id, actor_id, session)
    return list(
        session.scalars(
            select(ShopAdmin).where(ShopAdmin.shop_id == shop_id).order_by(ShopAdmin.user_id)
        ).all()
    )
