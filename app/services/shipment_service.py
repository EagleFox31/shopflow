from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import ShipmentStatus
from app.models.shipment import Shipment


def create_shipment(
    order_id: int,
    carrier: str,
    tracking_number: str | None,
    session: Session,
) -> Shipment:
    existing = session.scalar(select(Shipment).where(Shipment.order_id == order_id))
    if existing:
        raise ConflictError("Shipment already exists for this order")
    if tracking_number:
        duplicate_tracking = session.scalar(
            select(Shipment).where(Shipment.tracking_number == tracking_number)
        )
        if duplicate_tracking:
            raise ConflictError("Tracking number already exists")
    shipment = Shipment(
        order_id=order_id,
        carrier=carrier,
        tracking_number=tracking_number,
        status=ShipmentStatus.SHIPPED,
        shipped_at=datetime.now(timezone.utc),
    )
    session.add(shipment)
    session.flush()
    return shipment


def get_shipment(order_id: int, session: Session) -> Shipment:
    shipment = session.scalar(select(Shipment).where(Shipment.order_id == order_id))
    if not shipment:
        raise NotFoundError("Shipment not found")
    return shipment


def mark_delivered(order_id: int, session: Session) -> Shipment:
    shipment = get_shipment(order_id, session)
    shipment.status = ShipmentStatus.DELIVERED
    shipment.delivered_at = datetime.now(timezone.utc)
    session.flush()
    return shipment


def mark_returned(order_id: int, session: Session) -> Shipment | None:
    shipment = session.scalar(select(Shipment).where(Shipment.order_id == order_id))
    if not shipment:
        return None
    shipment.status = ShipmentStatus.RETURNED
    session.flush()
    return shipment
