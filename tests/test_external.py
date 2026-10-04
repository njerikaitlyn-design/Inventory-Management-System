import pytest
import requests
from unittest.mock import patch, Mock

from openfoodfacts import (
    fetch_product_by_barcode,
    search_products_by_name,
    clean_product,
    ExternalAPIError,
)


def make_response(json_data=None, http_error=False):
    """Build a fake response that looks like what requests.get returns."""
    response = Mock()
    response.json.return_value = json_data
    if http_error:
        response.raise_for_status.side_effect = requests.HTTPError("503 error")
    return response

def test_clean_product_keeps_needed_fields():
    raw = {
        "code": "123",
        "product_name": "Test Milk",
        "brands": "TestCo",
        "ingredients_text": "milk",
        "extra_field": "should be dropped",
    }
    result = clean_product(raw)
    assert result == {
        "barcode": "123",
        "product_name": "Test Milk",
        "brands": "TestCo",
        "ingredients_text": "milk",
    }


def test_clean_product_fills_missing_fields():
    result = clean_product({})
    assert result == {
        "barcode": "",
        "product_name": "",
        "brands": "",
        "ingredients_text": "",
    }

@patch("openfoodfacts.requests.get")
def test_fetch_product_found(mock_get):
    mock_get.return_value = make_response({
        "status": 1,
        "product": {
            "code": "3017620422003",
            "product_name": "Nutella",
            "brands": "Ferrero",
            "ingredients_text": "sugar, palm oil",
        },
    })

    result = fetch_product_by_barcode("3017620422003")

    assert result["product_name"] == "Nutella"
    assert result["barcode"] == "3017620422003"


@patch("openfoodfacts.requests.get")
def test_fetch_sends_barcode_and_user_agent(mock_get):
    mock_get.return_value = make_response({"status": 0})

    fetch_product_by_barcode("3017620422003")

    args, kwargs = mock_get.call_args
    assert "3017620422003" in args[0]
    assert "User-Agent" in kwargs["headers"]


@patch("openfoodfacts.requests.get")
def test_fetch_product_not_found(mock_get):
    mock_get.return_value = make_response({"status": 0})
    assert fetch_product_by_barcode("0000000000000") is None


@patch("openfoodfacts.requests.get")
def test_fetch_connection_error(mock_get):
    mock_get.side_effect = requests.ConnectionError("no internet")
    with pytest.raises(ExternalAPIError):
        fetch_product_by_barcode("3017620422003")


@patch("openfoodfacts.requests.get")
def test_fetch_http_error(mock_get):
    mock_get.return_value = make_response(http_error=True)
    with pytest.raises(ExternalAPIError):
        fetch_product_by_barcode("3017620422003")


@patch("openfoodfacts.requests.get")
def test_fetch_invalid_json(mock_get):
    response = make_response()
    response.json.side_effect = ValueError("not json")
    mock_get.return_value = response
    with pytest.raises(ExternalAPIError):
        fetch_product_by_barcode("3017620422003") 

@patch("openfoodfacts.requests.get")
def test_search_returns_cleaned_list(mock_get):
    mock_get.return_value = make_response({
        "products": [
            {"code": "1", "product_name": "Nutella", "brands": "Ferrero",
             "ingredients_text": "sugar"},
            {"code": "2", "product_name": "Nutella B-ready", "brands": "Ferrero",
             "ingredients_text": "flour"},
        ]
    })

    results = search_products_by_name("nutella")

    assert len(results) == 2
    assert results[0]["barcode"] == "1"
    assert results[1]["product_name"] == "Nutella B-ready"


@patch("openfoodfacts.requests.get")
def test_search_no_results(mock_get):
    mock_get.return_value = make_response({"products": []})
    assert search_products_by_name("zzzzzz") == []


@patch("openfoodfacts.requests.get")
def test_search_uses_limit(mock_get):
    mock_get.return_value = make_response({"products": []})

    search_products_by_name("nutella", limit=3)

    _, kwargs = mock_get.call_args
    assert kwargs["params"]["page_size"] == 3
    assert kwargs["params"]["search_terms"] == "nutella"


@patch("openfoodfacts.requests.get")
def test_search_http_error(mock_get):
    mock_get.return_value = make_response(http_error=True)
    with pytest.raises(ExternalAPIError):
        search_products_by_name("nutella")           