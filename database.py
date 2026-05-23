# ─────────────────────────────────────────────
#  database.py — Product Price Database
#  Smart Cart Project
# ─────────────────────────────────────────────

products = {
    "012345678905": {"name": "Apple Juice 1L",   "price": 2.50},
    "987654321098": {"name": "Bread (White)",     "price": 1.80},
    "112233445566": {"name": "Milk 1L",           "price": 1.20},
    "223344556677": {"name": "Butter 250g",       "price": 3.00},
    "334455667788": {"name": "Eggs (12pcs)",      "price": 2.80},
    "445566778899": {"name": "Rice 1kg",          "price": 1.50},
    "556677889900": {"name": "Chicken 500g",      "price": 4.50},
    "667788990011": {"name": "Orange Juice 1L",   "price": 2.20},
    "778899001122": {"name": "Cheese 200g",       "price": 3.50},
    "889900112233": {"name": "Yogurt 500ml",      "price": 1.90},
}

def get_product(barcode):
    """Look up product by barcode. Returns dict or None."""
    return products.get(barcode, None)

def add_product(barcode, name, price):
    """Add a new product to the database."""
    products[barcode] = {"name": name, "price": round(float(price), 2)}
    print(f"[DB] Added: {name} @ ${price}")

def list_products():
    """Print all products in database."""
    print("\n── Product Database ──────────────────")
    for barcode, info in products.items():
        print(f"  {barcode}: {info['name']:<25} ${info['price']:.2f}")
    print("─────────────────────────────────────\n")
