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
