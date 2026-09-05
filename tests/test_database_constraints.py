import pytest
from sqlalchemy.exc import IntegrityError

from app.models.cart import Cart
from app.models.enums import CartStatus
from app.models.product import Product
from app.models.shop import Shop
from tests.conftest import IS_SQLITE, TestingSessionLocal


def test_database_enforces_one_active_cart_per_user_and_shop(user_factory, shop_factory):
    user = user_factory("constraint-cart@example.com")
    shop = shop_factory(user["headers"])

    with TestingSessionLocal() as session:
        session.add(
            Cart(
                user_id=user["user"]["id"],
                shop_id=shop["id"],
                status=CartStatus.ACTIVE,
            )
        )
        session.commit()

        session.add(
            Cart(
                user_id=user["user"]["id"],
                shop_id=shop["id"],
                status=CartStatus.ACTIVE,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        session.add(
            Cart(
                user_id=user["user"]["id"],
                shop_id=shop["id"],
                status=CartStatus.CONVERTED,
            )
        )
        session.commit()


def test_database_enforces_shop_scoped_sku_uniqueness(user_factory, shop_factory):
    user = user_factory("constraint-product@example.com")
    shop = shop_factory(user["headers"])

    with TestingSessionLocal() as session:
        session.add(
            Product(
                shop_id=shop["id"],
                name="One",
                sku="DB-UNIQUE",
                price=100,
                stock_quantity=1,
            )
        )
        session.commit()
        session.add(
            Product(
                shop_id=shop["id"],
                name="Two",
                sku="DB-UNIQUE",
                price=100,
                stock_quantity=1,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_postgres_enforces_foreign_keys():
    if IS_SQLITE:
        pytest.skip("SQLite unit mode does not enable FK enforcement; PostgreSQL CI covers it")

    with TestingSessionLocal() as session:
        session.add(
            Shop(
                owner_id=999999,
                name="Invalid FK Shop",
                slug="invalid-fk-shop",
                currency="XAF",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
