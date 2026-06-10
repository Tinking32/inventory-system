from app.models import Category, Product


def _seed(client):
    """Seed test data and return the TestClient."""
    client.post("/api/categories/", json={"name": "Electronics"})
    client.post("/api/categories/", json={"name": "Beverages"})
    client.post(
        "/api/products/",
        json={"name": "Wireless Mouse", "quantity": 5, "price": 29.99, "low_stock_threshold": 10, "category_id": 1},
    )
    client.post(
        "/api/products/",
        json={"name": "Gaming Monitor", "quantity": 50, "price": 499.00, "low_stock_threshold": 10, "category_id": 1},
    )
    client.post(
        "/api/products/",
        json={"name": "Coca Cola", "quantity": 200, "price": 1.50, "low_stock_threshold": 30, "category_id": 2},
    )


def test_low_stock(client):
    _seed(client)
    r = client.post("/api/ask/", json={"question": "which products are low on stock?"})
    assert r.status_code == 200
    data = r.json()
    assert data["query_type"] == "low_stock"
    assert data["mode"] == "mock"
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "Wireless Mouse"


def test_most_expensive(client):
    _seed(client)
    r = client.post("/api/ask/", json={"question": "what is the most expensive product?"})
    assert r.status_code == 200
    assert r.json()["query_type"] == "most_expensive"
    assert r.json()["results"][0]["name"] == "Gaming Monitor"


def test_cheapest(client):
    _seed(client)
    r = client.post("/api/ask/", json={"question": "what is the cheapest product?"})
    assert r.status_code == 200
    assert r.json()["query_type"] == "cheapest"
    assert r.json()["results"][0]["name"] == "Coca Cola"


def test_total_value(client):
    _seed(client)
    r = client.post("/api/ask/", json={"question": "what is the total value of inventory?"})
    assert r.status_code == 200
    assert r.json()["query_type"] == "total_value"
    assert r.json()["results"][0]["product_count"] == 3


def test_count(client):
    _seed(client)
    r = client.post("/api/ask/", json={"question": "how many products do we have?"})
    assert r.status_code == 200
    assert r.json()["query_type"] == "count"
    assert r.json()["results"][0]["total_products"] == 3


def test_category_filter(client):
    _seed(client)
    r = client.post("/api/ask/", json={"question": "list all products in Electronics"})
    assert r.status_code == 200
    assert r.json()["query_type"] == "category_filter"
    assert len(r.json()["results"]) == 2


def test_name_search(client):
    """Searching for a product by name should return product_detail when found."""
    _seed(client)
    r = client.post("/api/ask/", json={"question": "find mouse"})
    assert r.status_code == 200
    assert r.json()["query_type"] == "product_detail"
    assert r.json()["results"][0]["name"] == "Wireless Mouse"


def test_list_all(client):
    _seed(client)
    r = client.post("/api/ask/", json={"question": "show all products"})
    assert r.status_code == 200
    assert r.json()["query_type"] == "list_all"
    assert len(r.json()["results"]) == 3


def test_empty_question_rejected(client):
    r = client.post("/api/ask/", json={"question": ""})
    assert r.status_code == 422


def test_chinese_keywords(client):
    _seed(client)
    r = client.post("/api/ask/", json={"question": "哪些货快过期了？"})
    assert r.status_code == 200
    assert r.json()["query_type"] == "low_stock"
    assert r.json()["results"][0]["name"] == "Wireless Mouse"
