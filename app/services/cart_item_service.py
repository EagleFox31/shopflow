from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.services import cart_service, product_service


def _load_cart(cart_id: int, session: Session) -> Cart:
    cart = session.scalar(
        select(Cart).options(selectinload(Cart.items)).where(Cart.id == cart_id)
    )
    if not cart:
        raise NotFoundError("Cart not found")
    return cart


def add_or_update_item(
    cart_id: int,
    product_id: int,
    quantity: int,
    session: Session,
) -> Cart:
    cart = _load_cart(cart_id, session)
    product = product_service.get_product(cart.shop_id, product_id, session)
    product_service.check_availability(product, quantity)

    item = session.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product.id,
        )
    )
    if item:
        item.quantity = quantity
        item.unit_price = product.price
    else:
        session.add(
            CartItem(
                cart_id=cart.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price,
            )
        )
    session.flush()
    session.refresh(cart)
    cart = _load_cart(cart.id, session)
    cart_service.recalculate_total(cart, session)
    session.commit()
    return _load_cart(cart.id, session)


def remove_item(cart_id: int, product_id: int, session: Session) -> Cart:
    cart = _load_cart(cart_id, session)
    item = session.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id,
        )
    )
    if not item:
        raise NotFoundError("Cart item not found")
    session.delete(item)
    session.flush()
    cart = _load_cart(cart.id, session)
    cart_service.recalculate_total(cart, session)
    session.commit()
    return _load_cart(cart.id, session)


def validate_cart_owner(cart: Cart, user_id: int) -> None:
    if cart.user_id != user_id:
        raise ForbiddenError("Cart does not belong to current user")
