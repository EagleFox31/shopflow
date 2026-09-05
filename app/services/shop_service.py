from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.shop import Shop
from app.models.shop_admin import ShopAdmin
from app.schemas.shop import ShopCreate, ShopUpdate


def get_shop(shop_id: int, session: Session) -> Shop:
    shop = session.get(Shop, shop_id)
    if not shop:
        raise NotFoundError("Shop not found")
    return shop


def create_shop(owner_id: int, data: ShopCreate, session: Session) -> Shop:
    duplicate = session.scalar(
        select(Shop).where(Shop.owner_id == owner_id, Shop.slug == data.slug)
    )
    if duplicate:
        raise ConflictError("You already have a shop with this slug")
    shop = Shop(owner_id=owner_id, **data.model_dump())
    session.add(shop)
    session.commit()
    session.refresh(shop)
    return shop


def list_user_shops(user_id: int, session: Session) -> list[Shop]:
    statement = (
        select(Shop)
        .outerjoin(ShopAdmin, ShopAdmin.shop_id == Shop.id)
        .where(or_(Shop.owner_id == user_id, ShopAdmin.user_id == user_id))
        .distinct()
        .order_by(Shop.id)
    )
    return list(session.scalars(statement).all())


def update_shop(shop_id: int, actor_id: int, data: ShopUpdate, session: Session) -> Shop:
    shop = assert_shop_access(shop_id, actor_id, session, owner_only=True)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(shop, field, value)
    session.commit()
    session.refresh(shop)
    return shop


def close_shop(shop_id: int, actor_id: int, session: Session) -> Shop:
    shop = assert_shop_access(shop_id, actor_id, session, owner_only=True)
    shop.is_active = False
    session.commit()
    return shop


def assert_shop_access(
    shop_id: int,
    user_id: int,
    session: Session,
    *,
    owner_only: bool = False,
) -> Shop:
    shop = get_shop(shop_id, session)
    if shop.owner_id == user_id:
        return shop
    if owner_only:
        raise ForbiddenError("Only the shop owner can perform this action")
    admin = session.get(ShopAdmin, {"shop_id": shop_id, "user_id": user_id})
    if not admin:
        raise ForbiddenError("You do not have access to this shop")
    return shop


def assert_shop_permission(
    shop_id: int,
    user_id: int,
    permission: str,
    session: Session,
) -> Shop:
    shop = get_shop(shop_id, session)
    if shop.owner_id == user_id:
        return shop
    admin = session.get(ShopAdmin, {"shop_id": shop_id, "user_id": user_id})
    if not admin or not getattr(admin, permission, False):
        raise ForbiddenError(f"Missing shop permission: {permission}")
    return shop
