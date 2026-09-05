from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ForbiddenError, InvalidStateError, NotFoundError
from app.models.enums import OrderStatus
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderUpdate, ShipmentCreate
from app.services import (
    address_service,
    cart_service,
    notification_service,
    payment_service,
    product_service,
    shipment_service,
    shop_service,
)


def _load_order(order_id: int, session: Session) -> Order:
    order = session.scalar(
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.history),
            selectinload(Order.payments),
        )
        .where(Order.id == order_id)
    )
    if not order:
        raise NotFoundError("Order not found")
    return order


def _record_status(
    order: Order,
    new_status: OrderStatus,
    actor_id: int | None,
    session: Session,
    *,
    note: str | None = None,
) -> None:
    old_status = order.status
    order.status = new_status
    session.add(
        OrderStatusHistory(
            order_id=order.id,
            from_status=old_status,
            to_status=new_status,
            note=note,
            changed_by_user_id=actor_id,
        )
    )


def create_order(
    shop_id: int,
    customer_id: int,
    data: OrderCreate,
    session: Session,
) -> Order:
    shop = shop_service.get_shop(shop_id, session)
    if not shop.is_active:
        raise InvalidStateError("Shop is closed")

    address_service.validate_order_address(data.address_id, customer_id, session)
    cart = cart_service.get_active_cart(customer_id, shop_id, session)
    if not cart.items:
        raise InvalidStateError("Cannot create an order from an empty cart")

    order = Order(
        shop_id=shop_id,
        customer_id=customer_id,
        address_id=data.address_id,
        status=OrderStatus.PENDING,
        subtotal=cart.total_amount,
        total_amount=cart.total_amount,
        currency=shop.currency,
    )
    session.add(order)
    session.flush()

    for cart_item in cart.items:
        product = product_service.get_product(
            shop_id, cart_item.product_id, session, for_update=True
        )
        product_service.reserve_stock(product, cart_item.quantity, session)
        session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                sku=product.sku,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                line_total=cart_item.unit_price * cart_item.quantity,
            )
        )

    session.add(
        OrderStatusHistory(
            order_id=order.id,
            from_status=None,
            to_status=OrderStatus.PENDING,
            note="Order created from active cart",
            changed_by_user_id=customer_id,
        )
    )
    cart_service.close_cart_after_order(cart, session)
    session.commit()

    notification_service.emit(
        "order.created",
        customer_id,
        {"order_id": order.id, "shop_id": shop_id},
    )
    return _load_order(order.id, session)


def get_order(
    order_id: int,
    actor_id: int,
    session: Session,
) -> Order:
    order = _load_order(order_id, session)
    if order.customer_id == actor_id:
        return order
    shop_service.assert_shop_access(order.shop_id, actor_id, session)
    return order


def list_orders(
    shop_id: int,
    actor_id: int,
    session: Session,
    *,
    status: OrderStatus | None = None,
) -> list[Order]:
    shop_service.assert_shop_permission(shop_id, actor_id, "can_manage_orders", session)
    statement = (
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.history))
        .where(Order.shop_id == shop_id)
        .order_by(Order.id.desc())
    )
    if status:
        statement = statement.where(Order.status == status)
    return list(session.scalars(statement).unique().all())


def list_customer_orders(customer_id: int, session: Session) -> list[Order]:
    return list(
        session.scalars(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.history))
            .where(Order.customer_id == customer_id)
            .order_by(Order.id.desc())
        ).unique().all()
    )


def update_order(
    order_id: int,
    actor_id: int,
    data: OrderUpdate,
    session: Session,
) -> Order:
    order = get_order(order_id, actor_id, session)
    if order.status not in {OrderStatus.PENDING, OrderStatus.PAID}:
        raise InvalidStateError("Only pending or paid orders can be edited")
    if data.address_id is not None:
        address_service.validate_order_address(data.address_id, order.customer_id, session)
        order.address_id = data.address_id
    session.commit()
    return _load_order(order.id, session)


def cancel_order(
    order_id: int,
    actor_id: int,
    reason: str,
    session: Session,
) -> Order:
    order = get_order(order_id, actor_id, session)
    if order.status in {
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.RETURNED,
        OrderStatus.CANCELLED,
    }:
        raise InvalidStateError("This order can no longer be cancelled")

    for item in order.items:
        product = session.get(Product, item.product_id)
        if product:
            product_service.release_stock(product, item.quantity, session)

    payment_service.refund_order_payment(order.id, session)
    _record_status(
        order,
        OrderStatus.CANCELLED,
        actor_id,
        session,
        note=reason,
    )
    session.commit()
    notification_service.emit(
        "order.cancelled",
        order.customer_id,
        {"order_id": order.id, "reason": reason},
    )
    return _load_order(order.id, session)


def confirm_order(order_id: int, actor_id: int, session: Session) -> Order:
    order = _load_order(order_id, session)
    shop_service.assert_shop_permission(
        order.shop_id, actor_id, "can_manage_orders", session
    )
    if order.status != OrderStatus.PAID:
        raise InvalidStateError("Order must be paid before confirmation")
    _record_status(
        order,
        OrderStatus.CONFIRMED,
        actor_id,
        session,
        note="Payment verified and order confirmed",
    )
    session.commit()
    notification_service.emit(
        "order.confirmed",
        order.customer_id,
        {"order_id": order.id},
    )
    return _load_order(order.id, session)


def ship_order(
    order_id: int,
    actor_id: int,
    data: ShipmentCreate,
    session: Session,
) -> Order:
    order = _load_order(order_id, session)
    shop_service.assert_shop_permission(
        order.shop_id, actor_id, "can_manage_orders", session
    )
    if order.status != OrderStatus.CONFIRMED:
        raise InvalidStateError("Only confirmed orders can be shipped")

    shipment_service.create_shipment(
        order.id,
        carrier=data.carrier,
        tracking_number=data.tracking_number,
        session=session,
    )
    _record_status(
        order,
        OrderStatus.SHIPPED,
        actor_id,
        session,
        note=f"Shipment created via {data.carrier}",
    )
    session.commit()
    notification_service.emit(
        "order.shipped",
        order.customer_id,
        {"order_id": order.id, "tracking_number": data.tracking_number},
    )
    return _load_order(order.id, session)


def deliver_order(order_id: int, actor_id: int, session: Session) -> Order:
    order = _load_order(order_id, session)
    shop_service.assert_shop_permission(
        order.shop_id, actor_id, "can_manage_orders", session
    )
    if order.status != OrderStatus.SHIPPED:
        raise InvalidStateError("Only shipped orders can be delivered")

    shipment_service.mark_delivered(order.id, session)
    _record_status(
        order,
        OrderStatus.DELIVERED,
        actor_id,
        session,
        note="Order delivered",
    )
    session.commit()
    notification_service.emit(
        "order.delivered",
        order.customer_id,
        {"order_id": order.id},
    )
    return _load_order(order.id, session)


def return_order(
    order_id: int,
    customer_id: int,
    reason: str,
    session: Session,
) -> Order:
    order = _load_order(order_id, session)
    if order.customer_id != customer_id:
        raise ForbiddenError("Only the customer can request a return")
    if order.status != OrderStatus.DELIVERED:
        raise InvalidStateError("Only delivered orders can be returned")

    for item in order.items:
        product = session.get(Product, item.product_id)
        if product:
            product_service.release_stock(product, item.quantity, session)

    payment_service.refund_order_payment(order.id, session)
    shipment_service.mark_returned(order.id, session)
    _record_status(
        order,
        OrderStatus.RETURNED,
        customer_id,
        session,
        note=reason,
    )
    session.commit()
    notification_service.emit(
        "order.returned",
        customer_id,
        {"order_id": order.id, "reason": reason},
    )
    return _load_order(order.id, session)


def get_order_history(order_id: int, actor_id: int, session: Session):
    order = get_order(order_id, actor_id, session)
    return order.history
