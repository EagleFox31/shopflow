import os
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = os.getenv(
    "SHOPFLOW_TEST_DATABASE_URL",
    "sqlite+pysqlite:///:memory:",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = "test-secret-key-at-least-32-bytes-long"

from app import models  # noqa: E402,F401
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

IS_SQLITE = TEST_DATABASE_URL.startswith("sqlite")

engine_kwargs: dict = {"pool_pre_ping": True}
if IS_SQLITE:
    engine_kwargs.update(
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

engine = create_engine(TEST_DATABASE_URL, **engine_kwargs)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    if IS_SQLITE:
        Base.metadata.create_all(bind=engine)
    else:
        required = {"users", "shops", "products", "orders", "payments"}
        existing = set(inspect(engine).get_table_names())
        missing = required - existing
        if missing:
            raise RuntimeError(
                "PostgreSQL test schema is not migrated. Missing tables: "
                + ", ".join(sorted(missing))
            )
    yield
    if IS_SQLITE:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_database(prepare_test_database):
    if IS_SQLITE:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    else:
        table_names = [table.name for table in Base.metadata.sorted_tables]
        quoted = ", ".join(f'"{name}"' for name in table_names)
        with engine.begin() as connection:
            connection.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def user_factory(client: TestClient) -> Callable:
    counter = 0

    def create_user(
        email: str | None = None,
        *,
        full_name: str | None = None,
        password: str = "strong-password",
    ) -> dict:
        nonlocal counter
        counter += 1
        email = email or f"user{counter}@example.com"
        full_name = full_name or f"User {counter}"

        register = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": full_name,
                "password": password,
            },
        )
        assert register.status_code == 201, register.text

        login = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        assert login.status_code == 200, login.text
        tokens = login.json()
        return {
            "user": register.json(),
            "email": email,
            "password": password,
            "tokens": tokens,
            "headers": {"Authorization": f"Bearer {tokens['access_token']}"},
        }

    return create_user


@pytest.fixture
def owner(user_factory) -> dict:
    return user_factory("owner@example.com", full_name="Owner")


@pytest.fixture
def auth_header(owner) -> dict[str, str]:
    return owner["headers"]


@pytest.fixture
def shop_factory(client: TestClient) -> Callable:
    counter = 0

    def create_shop(headers: dict[str, str], *, name: str | None = None, slug: str | None = None):
        nonlocal counter
        counter += 1
        response = client.post(
            "/api/v1/shops/",
            headers=headers,
            json={
                "name": name or f"Shop {counter}",
                "slug": slug or f"shop-{counter}",
                "currency": "XAF",
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return create_shop


@pytest.fixture
def category_factory(client: TestClient) -> Callable:
    counter = 0

    def create_category(shop_id: int, headers: dict[str, str], *, name=None, slug=None):
        nonlocal counter
        counter += 1
        response = client.post(
            f"/api/v1/shops/{shop_id}/categories/",
            headers=headers,
            json={
                "name": name or f"Category {counter}",
                "slug": slug or f"category-{counter}",
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return create_category


@pytest.fixture
def product_factory(client: TestClient) -> Callable:
    counter = 0

    def create_product(
        shop_id: int,
        headers: dict[str, str],
        *,
        category_id: int | None = None,
        name: str | None = None,
        sku: str | None = None,
        price: str = "10000.00",
        stock_quantity: int = 10,
    ):
        nonlocal counter
        counter += 1
        response = client.post(
            f"/api/v1/shops/{shop_id}/products/",
            headers=headers,
            json={
                "category_id": category_id,
                "name": name or f"Product {counter}",
                "sku": sku or f"SKU-{counter}",
                "price": price,
                "stock_quantity": stock_quantity,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return create_product


@pytest.fixture
def address_factory(client: TestClient) -> Callable:
    counter = 0

    def create_address(headers: dict[str, str], *, is_default: bool = True):
        nonlocal counter
        counter += 1
        response = client.post(
            "/api/v1/addresses/",
            headers=headers,
            json={
                "label": f"Address {counter}",
                "recipient_name": "Customer",
                "phone": "+237600000000",
                "line1": f"Street {counter}",
                "city": "Douala",
                "country": "CM",
                "is_default": is_default,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return create_address
