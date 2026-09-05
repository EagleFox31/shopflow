from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import OrderStatus
from app.models.user import User
from app.schemas.order import (
    OrderCancel,
    OrderCreate,
    OrderHistoryRead,
    OrderRead,
    OrderUpdate,
    ReturnOrderRequest,
    ShipmentCreate,
)
from app.services import order_service

router = APIRouter(tags=["orders"])


@router.post("/shops/{shop_id}/orders", response_model=OrderRead, status_code=201)
def create_order(
    shop_id: int,
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return order_service.create_order(shop_id, current_user.id, data, session)


@router.get("/shops/{shop_id}/orders", response_model=list[OrderRead])
def list_shop_orders(
    shop_id: int,
    status: OrderStatus | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return order_service.list_orders(
        shop_id, current_user.id, session, status=status
    )


@router.get("/orders/mine", response_model=list[OrderRead])
def my_orders(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return order_service.list_customer_orders(current_user.id, session)


@router.get("/orders/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return order_service.get_order(order_id, current_user.id, session)


@router.patch("/orders/{order_id}", response_model=OrderRead)
def update_order(
    order_id: int,
    data: OrderUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return order_service.update_order(order_id, current_user.id, data, session)


@router.post("/orders/{order_id}/cancel", response_model=OrderRead)
def cancel_order(
    order_id: int,
    data: OrderCancel,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return order_service.cancel_order(
        order_id, current_user.id, data.reason, session
    )


@router.post("/orders/{order_id}/confirm", response_model=OrderRead)
def confirm_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return order_service.confirm_order(order_id, current_user.id, session)


@router.post("/orders/{order_id}/ship", response_model=OrderRead)
def ship_order(
    order_id: int,
    data: ShipmentCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return order_service.ship_order(order_id, current_user.id, data, session)


@router.post("/orders/{order_id}/deliver", response_model=OrderRead)
def deliver_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return order_service.deliver_order(order_id, current_user.id, session)


@router.post("/orders/{order_id}/return", response_model=OrderRead)
def return_order(
    order_id: int,
    data: ReturnOrderRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return order_service.return_order(
        order_id, current_user.id, data.reason, session
    )


@router.get("/orders/{order_id}/history", response_model=list[OrderHistoryRead])
def order_history(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return order_service.get_order_history(order_id, current_user.id, session)
