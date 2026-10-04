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

def show_menu():
    print("\n=== Inventory Management ===")
    print("1. View all items")
    print("2. View one item")
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
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please pick a number from the menu.")


if __name__ == "__main__":
    main()