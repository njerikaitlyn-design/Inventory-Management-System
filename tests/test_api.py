import pytest
from unittest.mock import patch

import app as app_module
from openfoodfacts import ExternalAPIError

SAMPLE_ITEMS = [
    {
        "id": 1,
        "barcode": "111",
        "product_name": "Test Cola",
        "brands": "TestCo",
        "ingredients_text": "water, sugar",
        "price": 1.5,
        "stock": 10,
    },
    {
        "id": 2,
        "barcode": "222",
        "product_name": "Test Spread",
        "brands": "TestCo",
        "ingredients_text": "sugar, cocoa",
        "price": 4.0,
        "stock": 5,
    },
]


@pytest.fixture
def client():
    """Give each test a fresh client and a clean, known inventory."""
    original = [dict(item) for item in app_module.inventory]
    app_module.inventory[:] = [dict(item) for item in SAMPLE_ITEMS]
    app_module.app.config["TESTING"] = True

    with app_module.app.test_client() as test_client:
        yield test_client

    app_module.inventory[:] = original

def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json()["message"] == "Inventory API is running"


def test_get_all_items(client):
    response = client.get("/inventory")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_get_one_item(client):
    response = client.get("/inventory/1")
    assert response.status_code == 200
    assert response.get_json()["product_name"] == "Test Cola"


def test_get_missing_item(client):
    response = client.get("/inventory/99")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Item not found" 

def test_add_item(client):
    response = client.post(
        "/inventory",
        json={"product_name": "Bread", "price": 1.2, "stock": 25},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == 3
    assert data["product_name"] == "Bread"
    assert len(client.get("/inventory").get_json()) == 3


def test_add_item_without_name(client):
    response = client.post("/inventory", json={"price": 2})
    assert response.status_code == 400
    assert response.get_json()["error"] == "product_name is required"


def test_update_item(client):
    response = client.patch("/inventory/1", json={"price": 2.0, "stock": 30})
    assert response.status_code == 200
    data = response.get_json()
    assert data["price"] == 2.0
    assert data["stock"] == 30
    assert data["product_name"] == "Test Cola"


def test_update_cannot_change_id(client):
    response = client.patch("/inventory/1", json={"id": 50})
    assert response.status_code == 200
    assert response.get_json()["id"] == 1


def test_update_missing_item(client):
    response = client.patch("/inventory/99", json={"price": 5})
    assert response.status_code == 404


def test_delete_item(client):
    response = client.delete("/inventory/1")
    assert response.status_code == 200
    assert client.get("/inventory/1").status_code == 404


def test_delete_missing_item(client):
    response = client.delete("/inventory/99")
    assert response.status_code == 404       