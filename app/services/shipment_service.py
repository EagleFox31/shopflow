from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.enums import ShipmentStatus
from app.models.shipment import Shipment


def create_shipment(
    order_id: int,
    carrier: str,
    tracking_number: str | None,
    session: Session,
) -> Shipment:
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
    shipment = session.query(Shipment).filter(Shipment.order_id == order_id).one_or_none()
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
    shipment = session.query(Shipment).filter(Shipment.order_id == order_id).one_or_none()
    if not shipment:
        return None
    shipment.status = ShipmentStatus.RETURNED
    session.flush()
    return shipment
