def _create_customer_order(client, owner, customer, shop_factory, product_factory, address_factory):
    shop = shop_factory(owner["headers"])
    product = product_factory(shop["id"], owner["headers"], stock_quantity=4)
    address = address_factory(customer["headers"])
    client.put(
        f"/api/v1/shops/{shop['id']}/cart/items",
        headers=customer["headers"],
        json={"product_id": product["id"], "quantity": 2},
    )
    order = client.post(
        f"/api/v1/shops/{shop['id']}/orders",
        headers=customer["headers"],
        json={"address_id": address["id"]},
    )
    assert order.status_code == 201
    return shop, product, order.json()


def test_payment_failure_then_success_and_full_return_flow(
    client, user_factory, shop_factory, product_factory, address_factory
):
    owner = user_factory("merchant@example.com")
    customer = user_factory("buyer@example.com")
    shop, product, order = _create_customer_order(
        client, owner, customer, shop_factory, product_factory, address_factory
    )

    payment = client.post(
        f"/api/v1/orders/{order['id']}/payments/",
        headers=customer["headers"],
        json={"provider": "manual"},
    )
    assert payment.status_code == 201
    payment_id = payment.json()["id"]

    failed = client.post(
        f"/api/v1/orders/{order['id']}/payments/{payment_id}/failure",
        headers=owner["headers"],
        json={"provider_payload": {"reason": "declined"}},
    )
    assert failed.status_code == 200
    assert failed.json()["status"] == "FAILED"

    succeeded = client.post(
        f"/api/v1/orders/{order['id']}/payments/{payment_id}/success",
        headers=owner["headers"],
        json={"reference": "PAY-RETURN-1"},
    )
    assert succeeded.status_code == 200
    assert succeeded.json()["status"] == "SUCCEEDED"

    confirm = client.post(
        f"/api/v1/orders/{order['id']}/confirm", headers=owner["headers"]
    )
    assert confirm.status_code == 200

    ship = client.post(
        f"/api/v1/orders/{order['id']}/ship",
        headers=owner["headers"],
        json={"carrier": "DHL", "tracking_number": "RETURN-TRACK-1"},
    )
    assert ship.status_code == 200

    deliver = client.post(
        f"/api/v1/orders/{order['id']}/deliver", headers=owner["headers"]
    )
    assert deliver.status_code == 200

    owner_cannot_return = client.post(
        f"/api/v1/orders/{order['id']}/return",
        headers=owner["headers"],
        json={"reason": "Merchant cannot impersonate buyer"},
    )
    assert owner_cannot_return.status_code == 403

    returned = client.post(
        f"/api/v1/orders/{order['id']}/return",
        headers=customer["headers"],
        json={"reason": "Defective item"},
    )
    assert returned.status_code == 200
    assert returned.json()["status"] == "RETURNED"

    restored = client.get(f"/api/v1/shops/{shop['id']}/products/{product['id']}")
    assert restored.json()["stock_quantity"] == 4

    history = client.get(
        f"/api/v1/orders/{order['id']}/history", headers=customer["headers"]
    )
    assert [entry["to_status"] for entry in history.json()] == [
        "PENDING",
        "PAID",
        "CONFIRMED",
        "SHIPPED",
        "DELIVERED",
        "RETURNED",
    ]


def test_payment_cannot_be_attached_to_the_wrong_order(
    client, user_factory, shop_factory, product_factory, address_factory
):
    owner = user_factory("pay-owner@example.com")
    customer = user_factory("pay-customer@example.com")

    _, _, order1 = _create_customer_order(
        client, owner, customer, shop_factory, product_factory, address_factory
    )
    # Create a second order in a different shop to prove payment/order isolation.
    shop2 = shop_factory(owner["headers"], slug="pay-shop-2")
    product2 = product_factory(shop2["id"], owner["headers"], sku="PAY-2")
    address2 = address_factory(customer["headers"], is_default=False)
    client.put(
        f"/api/v1/shops/{shop2['id']}/cart/items",
        headers=customer["headers"],
        json={"product_id": product2["id"], "quantity": 1},
    )
    order2 = client.post(
        f"/api/v1/shops/{shop2['id']}/orders",
        headers=customer["headers"],
        json={"address_id": address2["id"]},
    ).json()

    payment = client.post(
        f"/api/v1/orders/{order1['id']}/payments/",
        headers=customer["headers"],
        json={"provider": "manual"},
    ).json()

    mismatch = client.post(
        f"/api/v1/orders/{order2['id']}/payments/{payment['id']}/success",
        headers=owner["headers"],
        json={"reference": "WRONG-ORDER"},
    )
    assert mismatch.status_code == 404


def test_customer_cannot_self_approve_or_fail_manual_payment(
    client, user_factory, shop_factory, product_factory, address_factory
):
    owner = user_factory("merchant-security@example.com")
    customer = user_factory("buyer-security@example.com")
    _, _, order = _create_customer_order(
        client, owner, customer, shop_factory, product_factory, address_factory
    )

    payment = client.post(
        f"/api/v1/orders/{order['id']}/payments/",
        headers=customer["headers"],
        json={"provider": "manual"},
    ).json()

    self_success = client.post(
        f"/api/v1/orders/{order['id']}/payments/{payment['id']}/success",
        headers=customer["headers"],
        json={"reference": "SELF-APPROVE"},
    )
    assert self_success.status_code == 403

    self_failure = client.post(
        f"/api/v1/orders/{order['id']}/payments/{payment['id']}/failure",
        headers=customer["headers"],
        json={"provider_payload": {"reason": "fake"}},
    )
    assert self_failure.status_code == 403

    merchant_success = client.post(
        f"/api/v1/orders/{order['id']}/payments/{payment['id']}/success",
        headers=owner["headers"],
        json={"reference": "MERCHANT-APPROVED"},
    )
    assert merchant_success.status_code == 200


def test_paid_order_rejects_new_payment_and_second_success(
    client, user_factory, shop_factory, product_factory, address_factory
):
    owner = user_factory("merchant-pay@example.com")
    customer = user_factory("buyer-pay@example.com")
    _, _, order = _create_customer_order(
        client, owner, customer, shop_factory, product_factory, address_factory
    )

    first = client.post(
        f"/api/v1/orders/{order['id']}/payments/",
        headers=customer["headers"],
        json={"provider": "manual"},
    ).json()
    second = client.post(
        f"/api/v1/orders/{order['id']}/payments/",
        headers=customer["headers"],
        json={"provider": "manual"},
    ).json()

    success = client.post(
        f"/api/v1/orders/{order['id']}/payments/{first['id']}/success",
        headers=owner["headers"],
        json={"reference": "ONLY-SUCCESS"},
    )
    assert success.status_code == 200

    new_payment = client.post(
        f"/api/v1/orders/{order['id']}/payments/",
        headers=customer["headers"],
        json={"provider": "manual"},
    )
    assert new_payment.status_code == 422

    second_success = client.post(
        f"/api/v1/orders/{order['id']}/payments/{second['id']}/success",
        headers=owner["headers"],
        json={"reference": "SECOND-SUCCESS"},
    )
    assert second_success.status_code == 422
