REQUIRED_PATHS = {
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/users/me",
    "/api/v1/addresses/",
    "/api/v1/shops/",
    "/api/v1/shops/{shop_id}",
    "/api/v1/shops/{shop_id}/admins",
    "/api/v1/shops/{shop_id}/categories/",
    "/api/v1/shops/{shop_id}/products/",
    "/api/v1/shops/{shop_id}/cart/",
    "/api/v1/shops/{shop_id}/orders",
    "/api/v1/orders/{order_id}",
    "/api/v1/orders/{order_id}/confirm",
    "/api/v1/orders/{order_id}/ship",
    "/api/v1/orders/{order_id}/deliver",
    "/api/v1/orders/{order_id}/return",
    "/api/v1/orders/{order_id}/history",
    "/api/v1/orders/{order_id}/payments/",
    "/api/v1/admin/roles",
}


def test_openapi_document_is_valid_and_complete(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    document = response.json()

    assert document["openapi"].startswith("3.")
    assert document["info"]["title"] == "ShopFlow"
    assert REQUIRED_PATHS <= set(document["paths"])

    schemas = document["components"]["schemas"]
    for schema in [
        "UserCreate",
        "UserRead",
        "TokenPair",
        "ShopCreate",
        "ShopRead",
        "ProductCreate",
        "ProductRead",
        "CartRead",
        "OrderCreate",
        "OrderRead",
        "PaymentCreate",
        "PaymentRead",
    ]:
        assert schema in schemas

    user_read_properties = schemas["UserRead"]["properties"]
    assert "password" not in user_read_properties
    assert "hashed_password" not in user_read_properties


def test_openapi_declares_authentication_for_protected_routes(client):
    document = client.get("/openapi.json").json()
    assert "OAuth2PasswordBearer" in document["components"]["securitySchemes"]

    me_operation = document["paths"]["/api/v1/users/me"]["get"]
    assert me_operation["security"] == [{"OAuth2PasswordBearer": []}]

    public_catalog = document["paths"]["/api/v1/shops/{shop_id}/products/"]["get"]
    assert not public_catalog.get("security")
