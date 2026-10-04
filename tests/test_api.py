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

FAKE_PRODUCT = {
    "barcode": "333",
    "product_name": "Mock Product",
    "brands": "MockCo",
    "ingredients_text": "mock ingredients",
}


@patch("app.fetch_product_by_barcode")
def test_search_by_barcode(mock_fetch, client):
    mock_fetch.return_value = FAKE_PRODUCT
    response = client.get("/search?barcode=333")
    assert response.status_code == 200
    assert response.get_json()["product_name"] == "Mock Product"
    mock_fetch.assert_called_once_with("333")


@patch("app.fetch_product_by_barcode")
def test_search_barcode_not_found(mock_fetch, client):
    mock_fetch.return_value = None
    response = client.get("/search?barcode=000")
    assert response.status_code == 404


@patch("app.search_products_by_name")
def test_search_by_name(mock_search, client):
    mock_search.return_value = [FAKE_PRODUCT]
    response = client.get("/search?name=mock")
    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_search_without_parameters(client):
    response = client.get("/search")
    assert response.status_code == 400


@patch("app.fetch_product_by_barcode")
def test_search_api_failure(mock_fetch, client):
    mock_fetch.side_effect = ExternalAPIError("API down")
    response = client.get("/search?barcode=333")
    assert response.status_code == 502


@patch("app.fetch_product_by_barcode")
def test_import_item(mock_fetch, client):
    mock_fetch.return_value = FAKE_PRODUCT
    response = client.post(
        "/inventory/import",
        json={"barcode": "333", "price": 6.5, "stock": 8},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["product_name"] == "Mock Product"
    assert data["price"] == 6.5
    assert data["stock"] == 8
    assert len(client.get("/inventory").get_json()) == 3


@patch("app.fetch_product_by_barcode")
def test_import_product_not_found(mock_fetch, client):
    mock_fetch.return_value = None
    response = client.post("/inventory/import", json={"barcode": "000"})
    assert response.status_code == 404


def test_import_without_barcode(client):
    response = client.post("/inventory/import", json={"price": 5})
    assert response.status_code == 400


@patch("app.fetch_product_by_barcode")
def test_import_api_failure(mock_fetch, client):
    mock_fetch.side_effect = ExternalAPIError("API down")
    response = client.post("/inventory/import", json={"barcode": "333"})
    assert response.status_code == 502      