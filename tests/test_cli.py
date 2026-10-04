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

# ---------- add_item ----------

@patch("cli.requests.request")
def test_add_item_success(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["Bread", "Sasko", "999", "1.2", "25"])
    mock_request.return_value = make_response(201, NEW_ITEM)

    cli.add_item()

    mock_request.assert_called_once_with(
        "POST",
        f"{cli.API_URL}/inventory",
        timeout=10,
        json={
            "product_name": "Bread",
            "brands": "Sasko",
            "barcode": "999",
            "price": 1.2,
            "stock": 25,
        },
    )
    output = capsys.readouterr().out
    assert "Item added" in output
    assert "Bread" in output


@patch("cli.requests.request")
def test_add_item_empty_name(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, [""])
    cli.add_item()
    assert "Product name cannot be empty." in capsys.readouterr().out
    mock_request.assert_not_called()


@patch("cli.requests.request")
def test_add_item_invalid_price(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["Bread", "Sasko", "", "abc"])
    cli.add_item()
    assert "Price must be a number" in capsys.readouterr().out
    mock_request.assert_not_called()


@patch("cli.requests.request")
def test_add_item_server_error(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["Bread", "Sasko", "", "1.2", "25"])
    mock_request.return_value = make_response(
        400, {"error": "product_name is required"}
    )
    cli.add_item()
    assert "Error: product_name is required" in capsys.readouterr().out


# ---------- update_item ----------

@patch("cli.requests.request")
def test_update_item_price_only(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["1", "2.5", ""])
    mock_request.return_value = make_response(200, ITEM)

    cli.update_item()

    mock_request.assert_called_once_with(
        "PATCH", f"{cli.API_URL}/inventory/1", timeout=10, json={"price": 2.5}
    )
    assert "Item updated" in capsys.readouterr().out


@patch("cli.requests.request")
def test_update_item_non_numeric_id(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["abc"])
    cli.update_item()
    assert "The ID must be a number." in capsys.readouterr().out
    mock_request.assert_not_called()


@patch("cli.requests.request")
def test_update_item_nothing_to_update(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["1", "", ""])
    cli.update_item()
    assert "Nothing to update." in capsys.readouterr().out
    mock_request.assert_not_called()


@patch("cli.requests.request")
def test_update_item_not_found(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["99", "5", ""])
    mock_request.return_value = make_response(404, {"error": "Item not found"})
    cli.update_item()
    assert "Item not found." in capsys.readouterr().out


@patch("cli.requests.request")
def test_update_item_invalid_price(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["1", "abc", ""])
    cli.update_item()
    assert "Price must be a number" in capsys.readouterr().out
    mock_request.assert_not_called()


# ---------- delete_item ----------

@patch("cli.requests.request")
def test_delete_item_confirmed(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["1", "y"])
    mock_request.return_value = make_response(200, {"message": "Item deleted"})

    cli.delete_item()

    mock_request.assert_called_once_with(
        "DELETE", f"{cli.API_URL}/inventory/1", timeout=10
    )
    assert "Item deleted." in capsys.readouterr().out


@patch("cli.requests.request")
def test_delete_item_cancelled(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["1", "n"])
    cli.delete_item()
    assert "Delete cancelled." in capsys.readouterr().out
    mock_request.assert_not_called()


@patch("cli.requests.request")
def test_delete_item_not_found(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["99", "y"])
    mock_request.return_value = make_response(404, {"error": "Item not found"})
    cli.delete_item()
    assert "Item not found." in capsys.readouterr().out


@patch("cli.requests.request")
def test_delete_item_non_numeric_id(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["abc"])
    cli.delete_item()
    assert "The ID must be a number." in capsys.readouterr().out
    mock_request.assert_not_called()        

# ---------- find_on_api ----------

@patch("cli.requests.request")
def test_find_by_barcode_then_skip_import(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["1", "333", ""])
    mock_request.return_value = make_response(200, PRODUCT)

    cli.find_on_api()

    assert "Mock Product" in capsys.readouterr().out
    mock_request.assert_called_once_with(
        "GET",
        f"{cli.API_URL}/search",
        timeout=10,
        params={"barcode": "333"},
    )


@patch("cli.requests.request")
def test_find_by_name_then_import(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["2", "mock", "1", "6.5", "8"])
    mock_request.side_effect = [
        make_response(200, [PRODUCT]),
        make_response(201, NEW_ITEM),
    ]

    cli.find_on_api()

    assert mock_request.call_count == 2
    second_call = mock_request.call_args_list[1]
    assert second_call.args[0] == "POST"
    assert second_call.args[1] == f"{cli.API_URL}/inventory/import"
    assert second_call.kwargs["json"] == {
        "barcode": "333",
        "price": 6.5,
        "stock": 8,
    }
    assert "Added to inventory" in capsys.readouterr().out


@patch("cli.requests.request")
def test_find_product_not_found(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["1", "000"])
    mock_request.return_value = make_response(404, {"error": "Product not found"})
    cli.find_on_api()
    assert "Error: Product not found" in capsys.readouterr().out


@patch("cli.requests.request")
def test_find_invalid_mode(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["9"])
    cli.find_on_api()
    assert "Invalid choice." in capsys.readouterr().out
    mock_request.assert_not_called()


@patch("cli.requests.request")
def test_find_empty_search(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["1", ""])
    cli.find_on_api()
    assert "The search cannot be empty." in capsys.readouterr().out
    mock_request.assert_not_called()


@patch("cli.requests.request")
def test_find_no_products(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["2", "zzzzzz"])
    mock_request.return_value = make_response(200, [])
    cli.find_on_api()
    assert "No products found." in capsys.readouterr().out


@patch("cli.requests.request")
def test_find_api_failure(mock_request, monkeypatch, capsys):
    feed_inputs(monkeypatch, ["2", "nutella"])
    mock_request.return_value = make_response(
        502, {"error": "Could not reach the OpenFoodFacts API"}
    )
    cli.find_on_api()
    assert "Could not reach" in capsys.readouterr().out


# ---------- main menu ----------

def test_main_exit(monkeypatch, capsys):
    feed_inputs(monkeypatch, ["0"])
    cli.main()
    assert "Goodbye!" in capsys.readouterr().out


def test_main_invalid_choice(monkeypatch, capsys):
    feed_inputs(monkeypatch, ["7", "0"])
    cli.main()
    assert "Invalid choice" in capsys.readouterr().out


@patch("cli.view_all_items")
def test_main_calls_view_all(mock_view_all, monkeypatch):
    feed_inputs(monkeypatch, ["1", "0"])
    cli.main()
    mock_view_all.assert_called_once()


def test_main_rejects_non_numeric_id(monkeypatch, capsys):
    feed_inputs(monkeypatch, ["2", "abc", "0"])
    cli.main()
    assert "The ID must be a number." in capsys.readouterr().out    