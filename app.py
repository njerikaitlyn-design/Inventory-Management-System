from flask import Flask, jsonify, request

from openfoodfacts import (
    fetch_product_by_barcode,
    search_products_by_name,
    ExternalAPIError,
)


app = Flask(__name__)

inventory = [
    {
        "id": 1,
        "barcode": "5449000000996",
        "product_name": "Coca-Cola Original",
        "brands": "Coca-Cola",
        "ingredients_text": "Carbonated water, sugar, colour, acid, flavourings",
        "price": 1.50,
        "stock": 40,
    },
    {
        "id": 2,
        "barcode": "3017620422003",
        "product_name": "Nutella",
        "brands": "Ferrero",
        "ingredients_text": "Sugar, palm oil, hazelnuts, cocoa, skim milk powder",
        "price": 4.25,
        "stock": 15,
    },
]

@app.route("/inventory", methods=["GET"])
def get_inventory():
    return jsonify(inventory), 200

@app.route("/inventory/<int:item_id>", methods=["GET"])
def get_item(item_id):
    for item in inventory:
        if item["id"] == item_id:
            return jsonify(item), 200
    return jsonify({"error": "Item not found"}), 404

@app.route("/")
def home():
    return jsonify({"message": "Inventory API is running"}), 200

@app.route("/inventory", methods=["POST"])
def add_item():
    data = request.get_json()

    if not data or "product_name" not in data:
        return jsonify({"error": "product_name is required"}), 400

    new_id = max((item["id"] for item in inventory), default=0) + 1

    new_item = {
        "id": new_id,
        "barcode": data.get("barcode", ""),
        "product_name": data["product_name"],
        "brands": data.get("brands", ""),
        "ingredients_text": data.get("ingredients_text", ""),
        "price": data.get("price", 0),
        "stock": data.get("stock", 0),
    }

    inventory.append(new_item)
    return jsonify(new_item), 201

@app.route("/inventory/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    allowed_fields = ["barcode", "product_name", "brands",
                      "ingredients_text", "price", "stock"]

    for item in inventory:
        if item["id"] == item_id:
            for field in allowed_fields:
                if field in data:
                    item[field] = data[field]
            return jsonify(item), 200

    return jsonify({"error": "Item not found"}), 404

@app.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    for item in inventory:
        if item["id"] == item_id:
            inventory.remove(item)
            return jsonify({"message": "Item deleted"}), 200

    return jsonify({"error": "Item not found"}), 404

@app.route("/search", methods=["GET"])
def search_external():
    barcode = request.args.get("barcode")
    name = request.args.get("name")

    if not barcode and not name:
        return jsonify({"error": "Provide a barcode or a name"}), 400

    try:
        if barcode:
            product = fetch_product_by_barcode(barcode)
            if product is None:
                return jsonify({"error": "Product not found"}), 404
            return jsonify(product), 200

        results = search_products_by_name(name)
        return jsonify(results), 200
    except ExternalAPIError as error:
        return jsonify({"error": str(error)}), 502
    
@app.route("/inventory/import", methods=["POST"])
def import_item():
    data = request.get_json()

    if not data or "barcode" not in data:
        return jsonify({"error": "barcode is required"}), 400

    try:
        product = fetch_product_by_barcode(data["barcode"])
    except ExternalAPIError as error:
        return jsonify({"error": str(error)}), 502

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    new_id = max((item["id"] for item in inventory), default=0) + 1

    new_item = {
        "id": new_id,
        "barcode": product["barcode"],
        "product_name": product["product_name"],
        "brands": product["brands"],
        "ingredients_text": product["ingredients_text"],
        "price": data.get("price", 0),
        "stock": data.get("stock", 0),
    }

    inventory.append(new_item)
    return jsonify(new_item), 201
   
    
if __name__ == "__main__":
    app.run(debug=True)
