from flask import Flask, jsonify

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

if __name__ == "__main__":
    app.run(debug=True)
