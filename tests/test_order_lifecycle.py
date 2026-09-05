def test_order_lifecycle_from_cart_to_delivery(client, auth_header):
    shop = client.post(
        "/api/v1/shops/",
        headers=auth_header,
        json={"name": "Main Shop", "slug": "main-shop", "currency": "XAF"},
    ).json()
    shop_id = shop["id"]

    category = client.post(
        f"/api/v1/shops/{shop_id}/categories/",
        headers=auth_header,
        json={"name": "Laptops", "slug": "laptops"},
    ).json()

    product = client.post(
        f"/api/v1/shops/{shop_id}/products/",
        headers=auth_header,
        json={
            "category_id": category["id"],
            "name": "ThinkPad",
            "sku": "LAP-001",
            "price": "1000000.00",
            "stock_quantity": 5,
        },
    ).json()

    address = client.post(
        "/api/v1/addresses/",
        headers=auth_header,
        json={
            "label": "Home",
            "recipient_name": "Owner",
            "phone": "+237600000000",
            "line1": "Bonapriso",
            "city": "Douala",
            "country": "CM",
            "is_default": True,
        },
    ).json()

    cart = client.put(
        f"/api/v1/shops/{shop_id}/cart/items",
        headers=auth_header,
        json={"product_id": product["id"], "quantity": 2},
    )
    assert cart.status_code == 200

    order = client.post(
        f"/api/v1/shops/{shop_id}/orders",
        headers=auth_header,
        json={"address_id": address["id"]},
    )
    assert order.status_code == 201
    order_id = order.json()["id"]
    assert order.json()["status"] == "PENDING"

    payment = client.post(
        f"/api/v1/orders/{order_id}/payments/",
        headers=auth_header,
        json={"provider": "manual"},
    ).json()

    paid = client.post(
        f"/api/v1/orders/{order_id}/payments/{payment['id']}/success",
        headers=auth_header,
        json={"reference": "PAY-001"},
    )
    assert paid.status_code == 200

    confirmed = client.post(
        f"/api/v1/orders/{order_id}/confirm",
        headers=auth_header,
    )
    assert confirmed.json()["status"] == "CONFIRMED"

    shipped = client.post(
        f"/api/v1/orders/{order_id}/ship",
        headers=auth_header,
        json={"carrier": "DHL", "tracking_number": "TRACK-001"},
    )
    assert shipped.json()["status"] == "SHIPPED"

    delivered = client.post(
        f"/api/v1/orders/{order_id}/deliver",
        headers=auth_header,
    )
    assert delivered.json()["status"] == "DELIVERED"

    history = client.get(
        f"/api/v1/orders/{order_id}/history",
        headers=auth_header,
    )
    assert [entry["to_status"] for entry in history.json()] == [
        "PENDING",
        "PAID",
        "CONFIRMED",
        "SHIPPED",
        "DELIVERED",
    ]
