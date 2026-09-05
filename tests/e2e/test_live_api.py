import os
from uuid import uuid4

import httpx
import pytest

BASE_URL = os.getenv("SHOPFLOW_E2E_BASE_URL")
pytestmark = pytest.mark.skipif(
    not BASE_URL,
    reason="SHOPFLOW_E2E_BASE_URL is required for live HTTP E2E tests",
)


def _register_and_login(client: httpx.Client, prefix: str) -> dict:
    unique = uuid4().hex[:10]
    email = f"{prefix}-{unique}@example.com"
    password = "strong-password"
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": prefix.title(), "password": password},
    )
    assert register.status_code == 201, register.text

    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return {
        "user": register.json(),
        "headers": {"Authorization": f"Bearer {login.json()['access_token']}"},
    }


def test_live_postgres_api_end_to_end():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok", "database": "ok"}

        openapi = client.get("/openapi.json")
        assert openapi.status_code == 200
        assert "/api/v1/shops/{shop_id}/orders" in openapi.json()["paths"]

        merchant = _register_and_login(client, "merchant")
        customer = _register_and_login(client, "customer")

        slug = f"live-shop-{uuid4().hex[:8]}"
        shop_response = client.post(
            "/api/v1/shops/",
            headers=merchant["headers"],
            json={"name": "Live Shop", "slug": slug, "currency": "XAF"},
        )
        assert shop_response.status_code == 201, shop_response.text
        shop = shop_response.json()

        isolated = client.get(
            f"/api/v1/shops/{shop['id']}",
            headers=customer["headers"],
        )
        assert isolated.status_code == 403

        category = client.post(
            f"/api/v1/shops/{shop['id']}/categories/",
            headers=merchant["headers"],
            json={"name": "Laptops", "slug": f"laptops-{uuid4().hex[:6]}"},
        )
        assert category.status_code == 201, category.text

        product = client.post(
            f"/api/v1/shops/{shop['id']}/products/",
            headers=merchant["headers"],
            json={
                "category_id": category.json()["id"],
                "name": "ThinkPad Live",
                "sku": f"LIVE-{uuid4().hex[:8]}",
                "price": "1000000.00",
                "stock_quantity": 2,
            },
        )
        assert product.status_code == 201, product.text
        product = product.json()

        address = client.post(
            "/api/v1/addresses/",
            headers=customer["headers"],
            json={
                "label": "Home",
                "recipient_name": "Live Customer",
                "phone": "+237600000000",
                "line1": "Bonapriso",
                "city": "Douala",
                "country": "CM",
                "is_default": True,
            },
        )
        assert address.status_code == 201, address.text

        cart = client.put(
            f"/api/v1/shops/{shop['id']}/cart/items",
            headers=customer["headers"],
            json={"product_id": product["id"], "quantity": 2},
        )
        assert cart.status_code == 200, cart.text
        assert cart.json()["total_amount"] == "2000000.00"

        order = client.post(
            f"/api/v1/shops/{shop['id']}/orders",
            headers=customer["headers"],
            json={"address_id": address.json()["id"]},
        )
        assert order.status_code == 201, order.text
        order = order.json()
        assert order["status"] == "PENDING"

        stock_after_order = client.get(
            f"/api/v1/shops/{shop['id']}/products/{product['id']}"
        )
        assert stock_after_order.json()["stock_quantity"] == 0

        payment = client.post(
            f"/api/v1/orders/{order['id']}/payments/",
            headers=customer["headers"],
            json={"provider": "manual"},
        )
        assert payment.status_code == 201, payment.text
        payment = payment.json()

        forbidden_self_approval = client.post(
            f"/api/v1/orders/{order['id']}/payments/{payment['id']}/success",
            headers=customer["headers"],
            json={"reference": f"LIVE-PAY-{uuid4().hex[:8]}"},
        )
        assert forbidden_self_approval.status_code == 403

        payment_reference = f"LIVE-PAY-{uuid4().hex[:8]}"
        success = client.post(
            f"/api/v1/orders/{order['id']}/payments/{payment['id']}/success",
            headers=merchant["headers"],
            json={"reference": payment_reference},
        )
        assert success.status_code == 200, success.text
        assert success.json()["status"] == "SUCCEEDED"

        confirm = client.post(
            f"/api/v1/orders/{order['id']}/confirm",
            headers=merchant["headers"],
        )
        assert confirm.status_code == 200, confirm.text
        assert confirm.json()["status"] == "CONFIRMED"

        tracking = f"LIVE-TRACK-{uuid4().hex[:8]}"
        ship = client.post(
            f"/api/v1/orders/{order['id']}/ship",
            headers=merchant["headers"],
            json={"carrier": "DHL", "tracking_number": tracking},
        )
        assert ship.status_code == 200, ship.text
        assert ship.json()["status"] == "SHIPPED"

        deliver = client.post(
            f"/api/v1/orders/{order['id']}/deliver",
            headers=merchant["headers"],
        )
        assert deliver.status_code == 200, deliver.text
        assert deliver.json()["status"] == "DELIVERED"

        returned = client.post(
            f"/api/v1/orders/{order['id']}/return",
            headers=customer["headers"],
            json={"reason": "E2E return validation"},
        )
        assert returned.status_code == 200, returned.text
        assert returned.json()["status"] == "RETURNED"

        stock_after_return = client.get(
            f"/api/v1/shops/{shop['id']}/products/{product['id']}"
        )
        assert stock_after_return.json()["stock_quantity"] == 2

        history = client.get(
            f"/api/v1/orders/{order['id']}/history",
            headers=customer["headers"],
        )
        assert history.status_code == 200
        assert [entry["to_status"] for entry in history.json()] == [
            "PENDING",
            "PAID",
            "CONFIRMED",
            "SHIPPED",
            "DELIVERED",
            "RETURNED",
        ]
