def test_one_user_can_create_multiple_shops(client, auth_header):
    first = client.post(
        "/api/v1/shops/",
        headers=auth_header,
        json={"name": "Alpha Shop", "slug": "alpha-shop", "currency": "XAF"},
    )
    second = client.post(
        "/api/v1/shops/",
        headers=auth_header,
        json={"name": "Beta Shop", "slug": "beta-shop", "currency": "XAF"},
    )

    assert first.status_code == 201
    assert second.status_code == 201

    shops = client.get("/api/v1/shops/", headers=auth_header)
    assert shops.status_code == 200
    assert {shop["slug"] for shop in shops.json()} == {"alpha-shop", "beta-shop"}


def test_shop_access_is_isolated_and_permissions_are_enforced(
    client, user_factory, shop_factory, category_factory, product_factory
):
    owner = user_factory("owner-a@example.com")
    admin = user_factory("catalog-admin@example.com")
    outsider = user_factory("outsider@example.com")
    shop = shop_factory(owner["headers"], name="Secure Shop", slug="secure-shop")

    denied = client.get(f"/api/v1/shops/{shop['id']}", headers=outsider["headers"])
    assert denied.status_code == 403

    add_admin = client.post(
        f"/api/v1/shops/{shop['id']}/admins",
        headers=owner["headers"],
        json={
            "user_id": admin["user"]["id"],
            "can_manage_catalog": True,
            "can_manage_orders": False,
            "can_manage_users": False,
        },
    )
    assert add_admin.status_code == 201

    admin_access = client.get(f"/api/v1/shops/{shop['id']}", headers=admin["headers"])
    assert admin_access.status_code == 200

    category = category_factory(shop["id"], admin["headers"], slug="admin-category")
    product = product_factory(
        shop["id"], admin["headers"], category_id=category["id"], sku="ADMIN-1"
    )
    assert product["shop_id"] == shop["id"]

    owner_only = client.patch(
        f"/api/v1/shops/{shop['id']}",
        headers=admin["headers"],
        json={"name": "Hijacked"},
    )
    assert owner_only.status_code == 403

    orders_denied = client.get(
        f"/api/v1/shops/{shop['id']}/orders",
        headers=admin["headers"],
    )
    assert orders_denied.status_code == 403

    outsider_product_write = client.post(
        f"/api/v1/shops/{shop['id']}/products/",
        headers=outsider["headers"],
        json={"name": "Nope", "sku": "NOPE", "price": "1.00", "stock_quantity": 1},
    )
    assert outsider_product_write.status_code == 403


def test_catalog_entities_cannot_cross_shop_boundaries(
    client, owner, shop_factory, category_factory, product_factory
):
    shop_a = shop_factory(owner["headers"], slug="shop-a")
    shop_b = shop_factory(owner["headers"], slug="shop-b")
    category_a = category_factory(shop_a["id"], owner["headers"], slug="cat-a")
    product_a = product_factory(
        shop_a["id"], owner["headers"], category_id=category_a["id"], sku="A-1"
    )

    wrong_shop_product = client.get(
        f"/api/v1/shops/{shop_b['id']}/products/{product_a['id']}"
    )
    assert wrong_shop_product.status_code == 404

    cross_category = client.post(
        f"/api/v1/shops/{shop_b['id']}/products/",
        headers=owner["headers"],
        json={
            "category_id": category_a["id"],
            "name": "Crossed",
            "sku": "B-1",
            "price": "100.00",
            "stock_quantity": 1,
        },
    )
    assert cross_category.status_code == 404


def test_uniqueness_is_scoped_per_owner_and_shop(client, user_factory, shop_factory, product_factory):
    first_owner = user_factory("first-owner@example.com")
    second_owner = user_factory("second-owner@example.com")

    first_shop = shop_factory(first_owner["headers"], slug="same-slug")
    duplicate_same_owner = client.post(
        "/api/v1/shops/",
        headers=first_owner["headers"],
        json={"name": "Duplicate", "slug": "same-slug", "currency": "XAF"},
    )
    assert duplicate_same_owner.status_code == 409

    second_shop = shop_factory(second_owner["headers"], slug="same-slug")
    assert second_shop["slug"] == first_shop["slug"]

    product_factory(first_shop["id"], first_owner["headers"], sku="SAME-SKU")
    duplicate_sku = client.post(
        f"/api/v1/shops/{first_shop['id']}/products/",
        headers=first_owner["headers"],
        json={"name": "Duplicate SKU", "sku": "SAME-SKU", "price": "100.00"},
    )
    assert duplicate_sku.status_code == 409

    other_shop_product = product_factory(
        second_shop["id"], second_owner["headers"], sku="SAME-SKU"
    )
    assert other_shop_product["sku"] == "SAME-SKU"


def test_update_uniqueness_conflicts_are_translated_to_409(
    client, owner, shop_factory, category_factory, product_factory
):
    shop_one = shop_factory(owner["headers"], slug="first-shop")
    shop_two = shop_factory(owner["headers"], slug="second-shop")

    shop_conflict = client.patch(
        f"/api/v1/shops/{shop_two['id']}",
        headers=owner["headers"],
        json={"slug": "first-shop"},
    )
    assert shop_conflict.status_code == 409

    category_one = category_factory(shop_one["id"], owner["headers"], slug="category-one")
    category_two = category_factory(shop_one["id"], owner["headers"], slug="category-two")
    category_conflict = client.patch(
        f"/api/v1/shops/{shop_one['id']}/categories/{category_two['id']}",
        headers=owner["headers"],
        json={"slug": category_one["slug"]},
    )
    assert category_conflict.status_code == 409

    product_one = product_factory(shop_one["id"], owner["headers"], sku="UNIQUE-1")
    product_two = product_factory(shop_one["id"], owner["headers"], sku="UNIQUE-2")
    product_conflict = client.patch(
        f"/api/v1/shops/{shop_one['id']}/products/{product_two['id']}",
        headers=owner["headers"],
        json={"sku": product_one["sku"]},
    )
    assert product_conflict.status_code == 409
