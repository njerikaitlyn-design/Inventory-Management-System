import requests

BASE_URL = "https://world.openfoodfacts.org"
HEADERS = {"User-Agent": "InventoryManagementSystem/1.0 (student project)"}


class ExternalAPIError(Exception):
    """Raised when the OpenFoodFacts API can't be reached or fails."""


def clean_product(product):
    """Keep only the fields our inventory needs."""
    return {
        "barcode": product.get("code", ""),
        "product_name": product.get("product_name", ""),
        "brands": product.get("brands", ""),
        "ingredients_text": product.get("ingredients_text", ""),
    }


def fetch_product_by_barcode(barcode):
    """Return cleaned product details, or None if the barcode isn't found."""
    url = f"{BASE_URL}/api/v2/product/{barcode}.json"
    params = {"fields": "code,product_name,brands,ingredients_text"}

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        raise ExternalAPIError("Could not reach the OpenFoodFacts API")

    if data.get("status") != 1 or "product" not in data:
        return None

    return clean_product(data["product"])


def search_products_by_name(name, limit=5):
    """Return a list of cleaned products that match a name."""
    url = f"{BASE_URL}/cgi/search.pl"
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": limit,
        "fields": "code,product_name,brands,ingredients_text",
    }

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        raise ExternalAPIError("Could not reach the OpenFoodFacts API")

    return [clean_product(p) for p in data.get("products", [])]