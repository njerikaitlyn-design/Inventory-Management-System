import pytest
import requests
from unittest.mock import patch, Mock

import cli

ITEM = {
    "id": 1,
    "barcode": "111",
    "product_name": "Test Cola",
    "brands": "TestCo",
    "ingredients_text": "water, sugar",
    "price": 1.5,
    "stock": 10,
}

NEW_ITEM = {
    "id": 3,
    "barcode": "999",
    "product_name": "Bread",
    "brands": "Sasko",
    "ingredients_text": "",
    "price": 1.2,
    "stock": 25,
}

PRODUCT = {
    "barcode": "333",
    "product_name": "Mock Product",
    "brands": "MockCo",
    "ingredients_text": "mock ingredients",
}


def make_response(status_code=200, json_data=None):
    """Build a fake server response."""
    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_data
    return response


def feed_inputs(monkeypatch, answers):
    """Make each input() call return the next answer in the list."""
    answers = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

# ---------- send_request ----------

@patch("cli.requests.request")
def test_send_request_returns_response(mock_request):
    mock_request.return_value = make_response(200, {})
    result = cli.send_request("GET", "/inventory")
    assert result.status_code == 200
    mock_request.assert_called_once_with(
        "GET", f"{cli.API_URL}/inventory", timeout=10
    )


@patch("cli.requests.request")
def test_send_request_server_down(mock_request, capsys):
    mock_request.side_effect = requests.ConnectionError("down")
    assert cli.send_request("GET", "/inventory") is None
    assert "could not connect" in capsys.readouterr().out


# ---------- view_all_items ----------

@patch("cli.requests.get")
def test_view_all_items_prints_items(mock_get, capsys):
    mock_get.return_value = make_response(200, [ITEM])
    cli.view_all_items()
    output = capsys.readouterr().out
    assert "Test Cola" in output
    assert "TestCo" in output


@patch("cli.requests.get")
def test_view_all_items_empty(mock_get, capsys):
    mock_get.return_value = make_response(200, [])
    cli.view_all_items()
    assert "The inventory is empty." in capsys.readouterr().out


@patch("cli.requests.get")
def test_view_all_items_server_down(mock_get, capsys):
    mock_get.side_effect = requests.ConnectionError("down")
    cli.view_all_items()
    assert "could not connect" in capsys.readouterr().out


# ---------- view_item ----------

@patch("cli.requests.get")
def test_view_item_found(mock_get, capsys):
    mock_get.return_value = make_response(200, ITEM)
    cli.view_item(1)
    assert "Test Cola" in capsys.readouterr().out
    mock_get.assert_called_once_with(f"{cli.API_URL}/inventory/1", timeout=10)


@patch("cli.requests.get")
def test_view_item_not_found(mock_get, capsys):
    mock_get.return_value = make_response(404, {"error": "Item not found"})
    cli.view_item(99)
    assert "Item not found." in capsys.readouterr().out


@patch("cli.requests.get")
def test_view_item_server_down(mock_get, capsys):
    mock_get.side_effect = requests.ConnectionError("down")
    cli.view_item(1)
    assert "could not connect" in capsys.readouterr().out
    
        