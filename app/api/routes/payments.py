from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import (
    PaymentCreate,
    PaymentFailure,
    PaymentRead,
    PaymentSuccess,
)
from app.services import order_service, payment_service, shop_service

router = APIRouter(prefix="/orders/{order_id}/payments", tags=["payments"])


@router.post("/", response_model=PaymentRead, status_code=201)
def initiate_payment(
    order_id: int,
    data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    order = order_service.get_order(order_id, current_user.id, session)
    return payment_service.initiate_payment(order, data, session)


def _get_payment_for_order(payment_id: int, order_id: int, session: Session):
    payment = payment_service.get_payment(payment_id, session)
    if payment.order_id != order_id:
        raise NotFoundError("Payment not found for this order")
    return payment


@router.post("/{payment_id}/success", response_model=PaymentRead)
def mark_success(
    order_id: int,
    payment_id: int,
    data: PaymentSuccess,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    order = order_service.get_order(order_id, current_user.id, session)
    shop_service.assert_shop_permission(
        order.shop_id, current_user.id, "can_manage_orders", session
    )
    _get_payment_for_order(payment_id, order_id, session)
    return payment_service.mark_payment_success(payment_id, data, session)


@router.post("/{payment_id}/failure", response_model=PaymentRead)
def mark_failure(
    order_id: int,
    payment_id: int,
    data: PaymentFailure,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    order = order_service.get_order(order_id, current_user.id, session)
    shop_service.assert_shop_permission(
        order.shop_id, current_user.id, "can_manage_orders", session
    )
    _get_payment_for_order(payment_id, order_id, session)
    return payment_service.mark_payment_failed(
        payment_id, data.provider_payload, session
    )
