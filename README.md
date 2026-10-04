# Inventory Management System

A small retail inventory system made of a Flask REST API, a command-line
interface (CLI), and an integration with the OpenFoodFacts API. Employees
can add, view, update, and delete inventory items, and look up real product
details by barcode or name.

## Features

- Flask REST API with full CRUD (GET, POST, PATCH, DELETE)
- Look up products on OpenFoodFacts by barcode or name
- Import an OpenFoodFacts product straight into the inventory
- Menu-driven CLI with input validation and error handling
- Test suite built with pytest and unittest.mock
- Data is stored in a Python list (simulated storage), so it resets
  every time the server restarts

## Project Structure

```
inventory-management-system/
├── app.py              # Flask API and all routes
├── cli.py              # Command-line interface
├── openfoodfacts.py    # Functions that call the OpenFoodFacts API
├── pytest.ini          # Pytest configuration
├── requirements.txt    # Python dependencies
├── README.md
└── tests/
    ├── test_api.py       # Tests for the Flask routes
    ├── test_cli.py       # Tests for the CLI commands
    └── test_external.py  # Tests for the OpenFoodFacts functions
```

## Installation and Setup

1. Clone the repository:

```
   git clone https://github.com/njerikaitlyn-design/Inventory-Management-System.git
   cd Inventory-Management-System
```

2. Create and activate a virtual environment:

```
   python3 -m venv venv
   source venv/bin/activate
```

3. Install the dependencies:

```
   pip install -r requirements.txt
```

## Running the Project

You need two terminals, both with the virtual environment activated.

**Terminal 1: start the API server**

```
python3 app.py
```

The API runs at `http://127.0.0.1:5000`.

**Terminal 2: start the CLI**

```
python3 cli.py
```

## API Endpoints

| Method | Endpoint | Description | Success | Errors |
|--------|----------|-------------|---------|--------|
| GET | `/` | Check the API is running | 200 | |
| GET | `/inventory` | Get all items | 200 | |
| GET | `/inventory/<id>` | Get one item | 200 | 404 |
| POST | `/inventory` | Add a new item | 201 | 400 |
| PATCH | `/inventory/<id>` | Update an item | 200 | 400, 404 |
| DELETE | `/inventory/<id>` | Delete an item | 200 | 404 |
| GET | `/search?barcode=<code>` | Look up a product on OpenFoodFacts by barcode | 200 | 400, 404, 502 |
| GET | `/search?name=<text>` | Search OpenFoodFacts by name | 200 | 400, 502 |
| POST | `/inventory/import` | Fetch a product by barcode and add it to the inventory | 201 | 400, 404, 502 |

Status codes: `400` bad input, `404` not found, `502` the OpenFoodFacts
API failed.

### Item format

```json
{
  "id": 1,
  "barcode": "5449000000996",
  "product_name": "Coca-Cola Original",
  "brands": "Coca-Cola",
  "ingredients_text": "Carbonated water, sugar, colour, acid, flavourings",
  "price": 1.5,
  "stock": 40
}
```

### Example requests

Add an item (`product_name` is required):

```
curl -X POST http://127.0.0.1:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Orange Juice", "brands": "Tropicana", "price": 3.5, "stock": 20}'
```

Update price and stock (only the fields you send are changed):

```
curl -X PATCH http://127.0.0.1:5000/inventory/1 \
  -H "Content-Type: application/json" \
  -d '{"price": 2.0, "stock": 30}'
```

Delete an item:

```
curl -X DELETE http://127.0.0.1:5000/inventory/2
```

Import a product from OpenFoodFacts (you supply the price and stock):

```
curl -X POST http://127.0.0.1:5000/inventory/import \
  -H "Content-Type: application/json" \
  -d '{"barcode": "3017620422003", "price": 4.5, "stock": 12}'
```

## CLI Usage

Running `python3 cli.py` shows this menu:

```
=== Inventory Management ===
1. View all items
2. View one item
3. Add an item
4. Update an item
5. Delete an item
6. Find a product on OpenFoodFacts
0. Exit
```

| Option | What it does |
|--------|--------------|
| 1 | Prints every item in the inventory |
| 2 | Asks for an ID and prints that item |
| 3 | Asks for name, brand, barcode, price, and stock, then adds the item |
| 4 | Asks for an ID, then a new price and/or stock (press Enter to skip a field) |
| 5 | Asks for an ID and confirmation, then deletes the item |
| 6 | Searches OpenFoodFacts by barcode or name, with the option to add a result to the inventory |
| 0 | Exits the program |

Example session for option 6:

```
Choose an option: 6
1. Search by barcode
2. Search by name
Choose: 1
Enter the barcode: 3017620422003
Searching...

[1]
  Name:    Nutella
  Brand:   Nutella, Ferrero
  Barcode: 3017620422003

Enter a number to add it to your inventory (or press Enter to skip): 1
Price: 4.5
Stock: 12
```

The CLI checks input before sending it (empty names, non-numeric prices
and IDs, invalid menu choices) and prints a friendly message if the
server is not running or the OpenFoodFacts API fails.

## Running the Tests

```
pytest -v
```

The tests use `unittest.mock` to replace the OpenFoodFacts API and the
server, so they run offline and do not depend on any outside website.

## Notes on the OpenFoodFacts API

- No API key is needed, but requests include a descriptive `User-Agent`
  header, as OpenFoodFacts asks.
- The name search is sometimes slow or returns a `503` error when
  OpenFoodFacts is busy. The app handles this and returns a clear error.
  Barcode lookups are more reliable.
- OpenFoodFacts data is crowd-sourced, so some fields may be missing or
  in another language.

## Design Notes

Each feature was built on its own Git branch (`feature/get-routes`,
`feature/post-route`, `feature/patch-delete-routes`,
`feature/openfoodfacts`, `feature/cli`, `feature/tests`, `feature/docs`),
merged into `main` with a pull request, and then deleted.

## Author

Kaitlyn