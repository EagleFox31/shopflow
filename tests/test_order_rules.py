def _make_order(client, customer, shop, product, address):
    add = client.put(
        f"/api/v1/shops/{shop['id']}/cart/items",
        headers=customer["headers"],
        json={"product_id": product["id"], "quantity": 2},
    )
    assert add.status_code == 200, add.text
    order = client.post(
        f"/api/v1/shops/{shop['id']}/orders",
        headers=customer["headers"],
        json={"address_id": address["id"]},
    )
    assert order.status_code == 201, order.text
    return order.json()


def test_order_creation_reserves_stock_and_closes_cart(
    client, owner, shop_factory, product_factory, address_factory
):
    shop = shop_factory(owner["headers"])
    product = product_factory(shop["id"], owner["headers"], stock_quantity=5)
    address = address_factory(owner["headers"])

    order = _make_order(client, owner, shop, product, address)
    assert order["status"] == "PENDING"
    assert order["items"][0]["quantity"] == 2

    fresh_product = client.get(f"/api/v1/shops/{shop['id']}/products/{product['id']}")
    assert fresh_product.json()["stock_quantity"] == 3

    new_cart = client.get(f"/api/v1/shops/{shop['id']}/cart/", headers=owner["headers"])
    assert new_cart.status_code == 200
    assert new_cart.json()["status"] == "ACTIVE"
    assert new_cart.json()["items"] == []


def test_order_rejects_empty_cart_foreign_address_and_closed_shop(
    client, user_factory, shop_factory, product_factory, address_factory
):
    owner = user_factory("shop-owner@example.com")
    customer = user_factory("customer@example.com")
    other = user_factory("other@example.com")
    shop = shop_factory(owner["headers"])
    product = product_factory(shop["id"], owner["headers"], stock_quantity=5)
    customer_address = address_factory(customer["headers"])
    other_address = address_factory(other["headers"])

    empty = client.post(
        f"/api/v1/shops/{shop['id']}/orders",
        headers=customer["headers"],
        json={"address_id": customer_address["id"]},
    )
    assert empty.status_code == 404  # no active cart exists yet

    client.put(
        f"/api/v1/shops/{shop['id']}/cart/items",
        headers=customer["headers"],
        json={"product_id": product["id"], "quantity": 1},
    )
    foreign_address = client.post(
        f"/api/v1/shops/{shop['id']}/orders",
        headers=customer["headers"],
        json={"address_id": other_address["id"]},
    )
    assert foreign_address.status_code == 403

    closed = client.post(f"/api/v1/shops/{shop['id']}/close", headers=owner["headers"])
    assert closed.status_code == 200
    closed_order = client.post(
        f"/api/v1/shops/{shop['id']}/orders",
        headers=customer["headers"],
        json={"address_id": customer_address["id"]},
    )
    assert closed_order.status_code == 422


def test_invalid_order_state_transitions_are_rejected(
    client, owner, shop_factory, product_factory, address_factory
):
    shop = shop_factory(owner["headers"])
    product = product_factory(shop["id"], owner["headers"], stock_quantity=5)
    address = address_factory(owner["headers"])
    order = _make_order(client, owner, shop, product, address)

    confirm_unpaid = client.post(
        f"/api/v1/orders/{order['id']}/confirm", headers=owner["headers"]
    )
    assert confirm_unpaid.status_code == 422

    ship_unconfirmed = client.post(
        f"/api/v1/orders/{order['id']}/ship",
        headers=owner["headers"],
        json={"carrier": "DHL"},
    )
    assert ship_unconfirmed.status_code == 422

    deliver_unshipped = client.post(
        f"/api/v1/orders/{order['id']}/deliver", headers=owner["headers"]
    )
    assert deliver_unshipped.status_code == 422

    return_undelivered = client.post(
        f"/api/v1/orders/{order['id']}/return",
        headers=owner["headers"],
        json={"reason": "Not yet"},
    )
    assert return_undelivered.status_code == 422


def test_cancel_releases_stock_and_refunds_successful_payment(
    client, owner, shop_factory, product_factory, address_factory
):
    shop = shop_factory(owner["headers"])
    product = product_factory(shop["id"], owner["headers"], stock_quantity=5)
    address = address_factory(owner["headers"])
    order = _make_order(client, owner, shop, product, address)

    payment = client.post(
        f"/api/v1/orders/{order['id']}/payments/",
        headers=owner["headers"],
        json={"provider": "manual"},
    ).json()
    success = client.post(
        f"/api/v1/orders/{order['id']}/payments/{payment['id']}/success",
        headers=owner["headers"],
        json={"reference": "CANCEL-PAY"},
    )
    assert success.status_code == 200

    cancelled = client.post(
        f"/api/v1/orders/{order['id']}/cancel",
        headers=owner["headers"],
        json={"reason": "Customer changed mind"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"

    fresh_product = client.get(f"/api/v1/shops/{shop['id']}/products/{product['id']}")
    assert fresh_product.json()["stock_quantity"] == 5

    second_cancel = client.post(
        f"/api/v1/orders/{order['id']}/cancel",
        headers=owner["headers"],
        json={"reason": "Again"},
    )
    assert second_cancel.status_code == 422


def test_customer_cannot_manage_another_customers_order(
    client, user_factory, shop_factory, product_factory, address_factory
):
    owner = user_factory("owner@example.com")
    customer = user_factory("customer@example.com")
    outsider = user_factory("outsider@example.com")
    shop = shop_factory(owner["headers"])
    product = product_factory(shop["id"], owner["headers"])
    address = address_factory(customer["headers"])
    order = _make_order(client, customer, shop, product, address)

    denied = client.get(f"/api/v1/orders/{order['id']}", headers=outsider["headers"])
    assert denied.status_code == 403

    owner_access = client.get(f"/api/v1/orders/{order['id']}", headers=owner["headers"])
    assert owner_access.status_code == 200
