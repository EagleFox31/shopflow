from enum import StrEnum


class CartStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CONVERTED = "CONVERTED"
    ABANDONED = "ABANDONED"


class OrderStatus(StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class ShipmentStatus(StrEnum):
    PENDING = "PENDING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"
