"""Test automatici generati dal QA Engineer Agent."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_homepage_renders():
    resp = client.get("/")
    assert resp.status_code == 200


def test_item_crud_flow():
    resp = client.post(
        "/api/items",
        json={"name": "Articolo di test", "description": "demo", "price": 9.99, "category": "test"},
    )
    assert resp.status_code == 201
    item = resp.json()
    assert item["name"] == "Articolo di test"

    resp = client.get("/api/items")
    assert resp.status_code == 200
    assert any(i["id"] == item["id"] for i in resp.json())

    item_id = item["id"]
    resp = client.get(f"/api/items/{item_id}")
    assert resp.status_code == 200

    resp = client.delete(f"/api/items/{item_id}")
    assert resp.status_code == 204


def test_customer_crud_flow():
    resp = client.post("/api/customers", json={"name": "Mario Rossi", "email": "mario@example.com"})
    assert resp.status_code == 201
    customer = resp.json()
    assert customer["name"] == "Mario Rossi"

    resp = client.get("/api/customers")
    assert resp.status_code == 200
    assert any(c["id"] == customer["id"] for c in resp.json())


def test_order_flow():
    resp = client.post(
        "/api/items",
        json={"name": "Articolo ordine", "description": "demo", "price": 5.0, "category": "test"},
    )
    item_id = resp.json()["id"]

    resp = client.post(
        "/api/orders",
        json={"customer_name": "Cliente Test", "items": [{"item_id": item_id, "quantity": 2}]},
    )
    assert resp.status_code == 201
    order = resp.json()
    assert order["customer_name"] == "Cliente Test"
    assert order["status"] == "ricevuto"

    resp = client.get("/api/orders")
    assert resp.status_code == 200
    assert any(o["id"] == order["id"] for o in resp.json())

    order_id = order["id"]
    resp = client.patch(f"/api/orders/{order_id}/status", params={"status": "in preparazione"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in preparazione"


def test_order_rejects_unknown_item():
    resp = client.post(
        "/api/orders",
        json={"customer_name": "Cliente Test", "items": [{"item_id": 999999, "quantity": 1}]},
    )
    assert resp.status_code == 400
