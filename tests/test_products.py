def create_category(client, name="Laptops") -> int:
    response = client.post("/categories/", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


def test_product_crud(client):
    category_id = create_category(client)

    create_response = client.post(
        "/products/",
        json={
            "name": "ThinkPad T14",
            "description": "Business laptop",
            "price": "1200.00",
            "stock": 3,
            "category_id": category_id,
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    get_response = client.get(f"/products/{product_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "ThinkPad T14"

    list_response = client.get("/products/?skip=0&limit=10")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.put(f"/products/{product_id}", json={"stock": 5})
    assert update_response.status_code == 200
    assert update_response.json()["stock"] == 5

    delete_response = client.delete(f"/products/{product_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/products/{product_id}")
    assert missing_response.status_code == 404


def test_create_product_requires_existing_category(client):
    response = client.post(
        "/products/",
        json={
            "name": "Ghost product",
            "price": "10.00",
            "stock": 1,
            "category_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"
