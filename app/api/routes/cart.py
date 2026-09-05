from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.cart import CartItemUpsert, CartRead
from app.services import cart_item_service, cart_service

router = APIRouter(prefix="/shops/{shop_id}/cart", tags=["cart"])


@router.get("/", response_model=CartRead)
def get_cart(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return cart_service.get_or_create_active_cart(current_user.id, shop_id, session)


@router.put("/items", response_model=CartRead)
def upsert_item(
    shop_id: int,
    data: CartItemUpsert,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    cart = cart_service.get_or_create_active_cart(current_user.id, shop_id, session)
    return cart_item_service.add_or_update_item(
        cart.id, data.product_id, data.quantity, session
    )


@router.delete("/items/{product_id}", response_model=CartRead)
def remove_item(
    shop_id: int,
    product_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    cart = cart_service.get_active_cart(current_user.id, shop_id, session)
    return cart_item_service.remove_item(cart.id, product_id, session)


@router.delete("/", response_model=CartRead)
def clear_cart(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    cart = cart_service.get_active_cart(current_user.id, shop_id, session)
    return cart_service.clear_cart(cart, session)
