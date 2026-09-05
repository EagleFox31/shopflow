from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.models.cart import Cart
from app.models.enums import CartStatus
from app.services import shop_service


def get_or_create_active_cart(user_id: int, shop_id: int, session: Session) -> Cart:
    shop_service.get_shop(shop_id, session)
    cart = session.scalar(
        select(Cart)
        .options(selectinload(Cart.items))
        .where(
            Cart.user_id == user_id,
            Cart.shop_id == shop_id,
            Cart.status == CartStatus.ACTIVE,
        )
    )
    if cart:
        return cart
    cart = Cart(user_id=user_id, shop_id=shop_id, status=CartStatus.ACTIVE)
    session.add(cart)
    session.commit()
    session.refresh(cart)
    return cart


def get_active_cart(user_id: int, shop_id: int, session: Session) -> Cart:
    shop_service.get_shop(shop_id, session)
    cart = session.scalar(
        select(Cart)
        .options(selectinload(Cart.items))
        .where(
            Cart.user_id == user_id,
            Cart.shop_id == shop_id,
            Cart.status == CartStatus.ACTIVE,
        )
    )
    if not cart:
        raise NotFoundError("Active cart not found")
    return cart


def recalculate_total(cart: Cart, session: Session) -> Cart:
    cart.total_amount = sum(
        (item.unit_price * item.quantity for item in cart.items),
        start=Decimal("0.00"),
    )
    session.flush()
    return cart


def clear_cart(cart: Cart, session: Session) -> Cart:
    cart.items.clear()
    cart.total_amount = Decimal("0.00")
    session.commit()
    return cart


def close_cart_after_order(cart: Cart, session: Session) -> None:
    cart.status = CartStatus.CONVERTED
    session.flush()


def get_abandoned_carts(session: Session) -> list[Cart]:
    return list(
        session.scalars(
            select(Cart)
            .where(Cart.status == CartStatus.ABANDONED)
            .order_by(Cart.updated_at.desc())
        ).all()
    )
