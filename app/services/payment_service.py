from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidStateError, NotFoundError
from app.models.enums import OrderStatus, PaymentStatus
from app.models.order import Order
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentSuccess


def initiate_payment(order: Order, data: PaymentCreate, session: Session) -> Payment:
    if order.status not in {OrderStatus.PENDING, OrderStatus.PAID}:
        raise InvalidStateError("Payment can only be initiated for a pending order")
    payment = Payment(
        order_id=order.id,
        provider=data.provider,
        amount=order.total_amount,
        status=PaymentStatus.PENDING,
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


def get_payment(payment_id: int, session: Session) -> Payment:
    payment = session.get(Payment, payment_id)
    if not payment:
        raise NotFoundError("Payment not found")
    return payment


def mark_payment_success(
    payment_id: int,
    data: PaymentSuccess,
    session: Session,
) -> Payment:
    payment = get_payment(payment_id, session)
    if payment.status == PaymentStatus.SUCCEEDED:
        return payment
    if payment.status not in {PaymentStatus.PENDING, PaymentStatus.FAILED}:
        raise InvalidStateError("Payment cannot be marked as successful")
    payment.status = PaymentStatus.SUCCEEDED
    payment.reference = data.reference
    payment.provider_payload = data.provider_payload
    payment.paid_at = datetime.now(timezone.utc)

    order = session.get(Order, payment.order_id)
    if order and order.status == OrderStatus.PENDING:
        from app.models.order_status_history import OrderStatusHistory

        order.status = OrderStatus.PAID
        session.add(
            OrderStatusHistory(
                order_id=order.id,
                from_status=OrderStatus.PENDING,
                to_status=OrderStatus.PAID,
                note="Payment succeeded",
                changed_by_user_id=order.customer_id,
            )
        )

    session.commit()
    session.refresh(payment)
    return payment


def mark_payment_failed(payment_id: int, payload: dict | None, session: Session) -> Payment:
    payment = get_payment(payment_id, session)
    if payment.status == PaymentStatus.SUCCEEDED:
        raise InvalidStateError("A successful payment cannot be marked as failed")
    payment.status = PaymentStatus.FAILED
    payment.provider_payload = payload
    session.commit()
    return payment


def get_successful_payment(order_id: int, session: Session) -> Payment | None:
    return session.scalar(
        select(Payment)
        .where(
            Payment.order_id == order_id,
            Payment.status == PaymentStatus.SUCCEEDED,
        )
        .order_by(Payment.id.desc())
    )


def refund_order_payment(order_id: int, session: Session) -> Payment | None:
    payment = get_successful_payment(order_id, session)
    if not payment:
        return None
    payment.status = PaymentStatus.REFUNDED
    session.flush()
    return payment
