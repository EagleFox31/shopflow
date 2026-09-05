from dataclasses import dataclass


@dataclass(slots=True)
class NotificationEvent:
    event: str
    user_id: int
    payload: dict


def emit(event: str, user_id: int, payload: dict) -> NotificationEvent:
    """
    Domain hook used by ShopFlow services.

    The original architecture treated notifications as optional infrastructure.
    This function is deliberately transport-agnostic: email/SMS/push adapters can
    subscribe later without coupling order_service to a provider.
    """
    return NotificationEvent(event=event, user_id=user_id, payload=payload)
