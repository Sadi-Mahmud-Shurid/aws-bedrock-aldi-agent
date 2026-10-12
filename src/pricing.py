import csv
import math


def load_products(path):
    """Read the price CSV and return a list of product dicts."""
    products = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            products.append({
                "name": row["name"].strip().lower(),
                "category": row["category"].strip().lower(),
                "pack_size": float(row["pack_size"]),
                "unit": row["unit"].strip().lower(),
                "price_eur": float(row["price_eur"]),
            })
    return products


def price_per_base(product):
    """Price per 100 g/ml, or per single piece for countable items."""
    per_unit = product["price_eur"] / product["pack_size"]
    return per_unit if product["unit"] == "piece" else per_unit * 100


def filter_by_category(products, category=None):
    """Return all products, or only those in the given category."""
    if not category:
        return list(products)
    wanted = category.strip().lower()
    return [p for p in products if p["category"] == wanted]


def parse_items(text):
    """Turn 'chicken breast:700:g;eggs:6:piece' into a list of dicts."""
    items = []
    for entry in text.split(";"):
        entry = entry.strip()
        if not entry:
            continue  # tolerate a trailing semicolon
        parts = [part.strip() for part in entry.split(":")]
        if len(parts) != 3:
            raise ValueError(f"Bad entry '{entry}': expected name:amount:unit")
        name, amount_text, unit = parts
        try:
            amount = float(amount_text)
        except ValueError:
            raise ValueError(f"Bad amount in '{entry}': not a number") from None
        if amount <= 0:
            raise ValueError(f"Bad amount in '{entry}': must be above zero")
        items.append({"name": name.lower(), "amount": amount, "unit": unit.lower()})
    return items


def calculate_basket(products, items):
    """Work out packs to buy and the total cost for a list of needed items."""
    by_name = {p["name"]: p for p in products}
    needed = {}  # product name -> total amount needed across all entries
    unmatched = []

    for item in items:
        product = by_name.get(item["name"])
        if product is None:
            unmatched.append(f"{item['name']} (not in the price list)")
        elif item["unit"] != product["unit"]:
            unmatched.append(
                f"{item['name']} (sold in {product['unit']}, requested {item['unit']})"
            )
        else:
            needed[product["name"]] = needed.get(product["name"], 0) + item["amount"]

    lines = []
    total = 0.0
    for name, amount in needed.items():
        product = by_name[name]
        packs = math.ceil(amount / product["pack_size"])
        line_cost = packs * product["price_eur"]
        total += line_cost
        lines.append({
            "name": name,
            "amount_needed": amount,
            "packs": packs,
            "pack_size": product["pack_size"],
            "unit": product["unit"],
            "line_cost": round(line_cost, 2),
        })

    return {"lines": lines, "total_eur": round(total, 2), "unmatched": unmatched}