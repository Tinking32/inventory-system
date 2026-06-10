def test_list_products_empty(client):
    r = client.get("/api/products/")
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_create_product(client):
    r = client.post(
        "/api/products/", json={"name": "Test Widget", "quantity": 10, "price": 9.99}
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test Widget"
    assert data["quantity"] == 10
    assert data["is_low_stock"] is True


def test_get_product_404(client):
    r = client.get("/api/products/999")
    assert r.status_code == 404


def test_create_and_get(client):
    # Create
    r = client.post(
        "/api/products/",
        json={"name": "Gadget", "quantity": 100, "price": 49.99, "low_stock_threshold": 20},
    )
    assert r.status_code == 201
    pid = r.json()["id"]

    # Get
    r = client.get(f"/api/products/{pid}")
    assert r.status_code == 200
    assert r.json()["name"] == "Gadget"
    assert r.json()["is_low_stock"] is False


def test_update_product(client):
    # Create
    r = client.post(
        "/api/products/", json={"name": "Old Name", "quantity": 5, "price": 1.00}
    )
    pid = r.json()["id"]

    # Update
    r = client.put(f"/api/products/{pid}", json={"name": "New Name", "price": 2.50})
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"
    assert r.json()["price"] == 2.50
    assert r.json()["quantity"] == 5  # unchanged


def test_delete_product(client):
    r = client.post(
        "/api/products/", json={"name": "Temp", "quantity": 1, "price": 0.50}
    )
    pid = r.json()["id"]

    r = client.delete(f"/api/products/{pid}")
    assert r.status_code == 204

    r = client.get(f"/api/products/{pid}")
    assert r.status_code == 404


def test_list_pagination(client):
    for i in range(5):
        client.post(
            "/api/products/", json={"name": f"Item {i}", "quantity": i, "price": 1.00}
        )
    r = client.get("/api/products/?page=1&page_size=3")
    assert r.json()["page"] == 1
    assert len(r.json()["items"]) == 3

    r = client.get("/api/products/?page=2&page_size=3")
    assert len(r.json()["items"]) >= 2


def test_search(client):
    client.post(
        "/api/products/", json={"name": "Unique Gadget XYZ", "quantity": 1, "price": 1.00}
    )
    r = client.get("/api/products/?q=Unique")
    assert r.json()["total"] == 1
    r = client.get("/api/products/?q=ZZZZZZZ")
    assert r.json()["total"] == 0


def test_low_stock_filter(client):
    client.post(
        "/api/products/",
        json={"name": "Rare Item", "quantity": 2, "price": 99.00, "low_stock_threshold": 10},
    )
    client.post(
        "/api/products/",
        json={"name": "Plenty Item", "quantity": 500, "price": 1.00, "low_stock_threshold": 10},
    )
    r = client.get("/api/products/?low_stock_only=true")
    items = r.json()["items"]
    for item in items:
        assert item["is_low_stock"] is True
