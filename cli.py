import requests

API_URL = "http://127.0.0.1:5000"


def print_item(item):
    """Show one inventory item in a readable way."""
    print(f"ID: {item['id']}")
    print(f"  Name:    {item['product_name']}")
    print(f"  Brand:   {item['brands']}")
    print(f"  Price:   {item['price']}")
    print(f"  Stock:   {item['stock']}")
    print(f"  Barcode: {item['barcode']}")


def send_request(method, path, **kwargs):
    """Send a request to the server. Returns None if the server is unreachable."""
    try:
        return requests.request(method, f"{API_URL}{path}", timeout=10, **kwargs)
    except requests.RequestException:
        print("Error: could not connect to the server. Is it running?")
        return None

def view_all_items():
    """Ask the server for every item and print them."""
    try:
        response = requests.get(f"{API_URL}/inventory", timeout=10)
    except requests.RequestException:
        print("Error: could not connect to the server. Is it running?")
        return

    items = response.json()
    if not items:
        print("The inventory is empty.")
        return

    for item in items:
        print_item(item)
        print()


def view_item(item_id):
    """Ask the server for one item by its ID."""
    try:
        response = requests.get(f"{API_URL}/inventory/{item_id}", timeout=10)
    except requests.RequestException:
        print("Error: could not connect to the server. Is it running?")
        return

    if response.status_code == 404:
        print("Item not found.")
        return

    print_item(response.json())

def add_item():
    name = input("Product name: ").strip()
    if not name:
        print("Product name cannot be empty.")
        return

    brand = input("Brand: ").strip()
    barcode = input("Barcode (optional): ").strip()

    try:
        price = float(input("Price: "))
        stock = int(input("Stock: "))
    except ValueError:
        print("Price must be a number and stock must be a whole number.")
        return

    payload = {
        "product_name": name,
        "brands": brand,
        "barcode": barcode,
        "price": price,
        "stock": stock,
    }

    response = send_request("POST", "/inventory", json=payload)
    if response is None:
        return

    if response.status_code == 201:
        print("Item added:")
        print_item(response.json())
    else:
        print(f"Error: {response.json().get('error', 'Something went wrong')}")    

def update_item():
    item_id = input("Enter the ID of the item to update: ").strip()
    if not item_id.isdigit():
        print("The ID must be a number.")
        return

    print("Press Enter to skip a field you don't want to change.")
    new_price = input("New price: ").strip()
    new_stock = input("New stock: ").strip()

    payload = {}
    try:
        if new_price:
            payload["price"] = float(new_price)
        if new_stock:
            payload["stock"] = int(new_stock)
    except ValueError:
        print("Price must be a number and stock must be a whole number.")
        return

    if not payload:
        print("Nothing to update.")
        return

    response = send_request("PATCH", f"/inventory/{item_id}", json=payload)
    if response is None:
        return

    if response.status_code == 200:
        print("Item updated:")
        print_item(response.json())
    elif response.status_code == 404:
        print("Item not found.")
    else:
        print(f"Error: {response.json().get('error', 'Something went wrong')}")

def delete_item():
    item_id = input("Enter the ID of the item to delete: ").strip()
    if not item_id.isdigit():
        print("The ID must be a number.")
        return

    confirm = input(f"Are you sure you want to delete item {item_id}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Delete cancelled.")
        return

    response = send_request("DELETE", f"/inventory/{item_id}")
    if response is None:
        return

    if response.status_code == 200:
        print("Item deleted.")
    elif response.status_code == 404:
        print("Item not found.")
    else:
        print("Something went wrong.")
def print_product(product):
    """Show one product found on OpenFoodFacts."""
    print(f"  Name:    {product['product_name']}")
    print(f"  Brand:   {product['brands']}")
    print(f"  Barcode: {product['barcode']}")


def find_on_api():
    print("1. Search by barcode")
    print("2. Search by name")
    mode = input("Choose: ").strip()

    if mode == "1":
        value = input("Enter the barcode: ").strip()
        params = {"barcode": value}
    elif mode == "2":
        value = input("Enter the product name: ").strip()
        params = {"name": value}
    else:
        print("Invalid choice.")
        return

    if not value:
        print("The search cannot be empty.")
        return

    print("Searching...")
    response = send_request("GET", "/search", params=params)
    if response is None:
        return

    if response.status_code != 200:
        print(f"Error: {response.json().get('error', 'Something went wrong')}")
        return

    results = response.json()
    if isinstance(results, dict):
        results = [results]

    if not results:
        print("No products found.")
        return

    for number, product in enumerate(results, start=1):
        print(f"\n[{number}]")
        print_product(product)

    pick = input("\nEnter a number to add it to your inventory (or press Enter to skip): ").strip()
    if not pick:
        return

    if not pick.isdigit() or not 1 <= int(pick) <= len(results):
        print("Invalid choice.")
        return

    chosen = results[int(pick) - 1]
    if not chosen["barcode"]:
        print("This product has no barcode, so it can't be imported.")
        return

    try:
        price = float(input("Price: "))
        stock = int(input("Stock: "))
    except ValueError:
        print("Price must be a number and stock must be a whole number.")
        return

    payload = {"barcode": chosen["barcode"], "price": price, "stock": stock}
    response = send_request("POST", "/inventory/import", json=payload)
    if response is None:
        return

    if response.status_code == 201:
        print("Added to inventory:")
        print_item(response.json())
    else:
        print(f"Error: {response.json().get('error', 'Something went wrong')}")

def show_menu():
    print("\n=== Inventory Management ===")
    print("1. View all items")
    print("2. View one item")
    print("3. Add an item")
    print("4. Update an item")
    print("5. Delete an item")
    print("6. Find a product on OpenFoodFacts")
    print("0. Exit")


def main():
    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            view_all_items()
        elif choice == "2":
            item_id = input("Enter the item ID: ").strip()
            if not item_id.isdigit():
                print("The ID must be a number.")
                continue
            view_item(int(item_id))
        elif choice == "3":
            add_item()
        elif choice == "4":
            update_item()
        elif choice == "5":
            delete_item()
        elif choice == "6":
            find_on_api()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please pick a number from the menu.")


if __name__ == "__main__":
    main()