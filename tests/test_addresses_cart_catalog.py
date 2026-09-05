def test_default_address_and_ownership(client, user_factory, address_factory):
    first = user_factory("address-one@example.com")
    second = user_factory("address-two@example.com")

    address_one = address_factory(first["headers"], is_default=True)
    address_two = address_factory(first["headers"], is_default=True)

    addresses = client.get("/api/v1/addresses/", headers=first["headers"])
    assert addresses.status_code == 200
    defaults = [item for item in addresses.json() if item["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == address_two["id"]

    forbidden_update = client.patch(
        f"/api/v1/addresses/{address_one['id']}",
        headers=second["headers"],
        json={"city": "Yaounde"},
    )
    assert forbidden_update.status_code == 403


def test_cart_totals_stock_validation_and_clear(
    client, owner, shop_factory, category_factory, product_factory
):
    shop = shop_factory(owner["headers"])
    category = category_factory(shop["id"], owner["headers"])
    product = product_factory(
        shop["id"],
        owner["headers"],
        category_id=category["id"],
        price="25000.00",
        stock_quantity=3,
    )

    empty = client.get(f"/api/v1/shops/{shop['id']}/cart/", headers=owner["headers"])
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["total_amount"] in ["0.00", "0"]

    too_many = client.put(
        f"/api/v1/shops/{shop['id']}/cart/items",
        headers=owner["headers"],
        json={"product_id": product["id"], "quantity": 4},
    )
    assert too_many.status_code == 422
    assert "Insufficient stock" in too_many.json()["detail"]

    added = client.put(
        f"/api/v1/shops/{shop['id']}/cart/items",
        headers=owner["headers"],
        json={"product_id": product["id"], "quantity": 2},
    )
    assert added.status_code == 200
    assert added.json()["items"][0]["quantity"] == 2
    assert added.json()["total_amount"] == "50000.00"

    updated = client.put(
        f"/api/v1/shops/{shop['id']}/cart/items",
        headers=owner["headers"],
        json={"product_id": product["id"], "quantity": 1},
    )
    assert updated.status_code == 200
    assert updated.json()["total_amount"] == "25000.00"

    cleared = client.delete(f"/api/v1/shops/{shop['id']}/cart/", headers=owner["headers"])
    assert cleared.status_code == 200
    assert cleared.json()["items"] == []
    assert cleared.json()["total_amount"] == "0.00"


def test_category_cannot_be_deleted_while_it_contains_products(
    client, owner, shop_factory, category_factory, product_factory
):
    shop = shop_factory(owner["headers"])
    category = category_factory(shop["id"], owner["headers"])
    product_factory(shop["id"], owner["headers"], category_id=category["id"])

    response = client.delete(
        f"/api/v1/shops/{shop['id']}/categories/{category['id']}",
        headers=owner["headers"],
    )
    assert response.status_code == 409


def test_product_delete_is_soft_delete_and_public_listing_hides_it(
    client, owner, shop_factory, product_factory
):
    shop = shop_factory(owner["headers"])
    product = product_factory(shop["id"], owner["headers"], sku="SOFT-1")

    deleted = client.delete(
        f"/api/v1/shops/{shop['id']}/products/{product['id']}",
        headers=owner["headers"],
    )
    assert deleted.status_code == 204

    listing = client.get(f"/api/v1/shops/{shop['id']}/products/")
    assert listing.status_code == 200
    assert listing.json() == []

    direct = client.get(f"/api/v1/shops/{shop['id']}/products/{product['id']}")
    assert direct.status_code == 200
    assert direct.json()["is_active"] is False


def test_cart_for_unknown_shop_returns_404_instead_of_database_error(client, owner):
    response = client.get("/api/v1/shops/999999/cart/", headers=owner["headers"])
    assert response.status_code == 404
    assert response.json() == {"detail": "Shop not found"}


def test_address_used_by_order_cannot_be_deleted(
    client, owner, shop_factory, product_factory, address_factory
):
    shop = shop_factory(owner["headers"])
    product = product_factory(shop["id"], owner["headers"], stock_quantity=2)
    address = address_factory(owner["headers"])
    client.put(
        f"/api/v1/shops/{shop['id']}/cart/items",
        headers=owner["headers"],
        json={"product_id": product["id"], "quantity": 1},
    )
    order = client.post(
        f"/api/v1/shops/{shop['id']}/orders",
        headers=owner["headers"],
        json={"address_id": address["id"]},
    )
    assert order.status_code == 201

    deleted = client.delete(f"/api/v1/addresses/{address['id']}", headers=owner["headers"])
    assert deleted.status_code == 409
    assert deleted.json()["detail"] == "Cannot delete an address used by an order"
