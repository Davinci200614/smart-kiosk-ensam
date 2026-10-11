"""Seed the JSON inventory for the kiosk menu."""

from __future__ import annotations

from backend.models_json import Produit
from backend.storage_json import load_inventory, save_inventory


def seed_produits() -> None:
    """Populate JSON inventory with the default menu if needed."""
    menu_items = [
        ("Sandwich Bocadillos", "🥪 Sandwiches & Savory Snacks", 28.0),
        ("Sandwich Kefta", "🥪 Sandwiches & Savory Snacks", 32.0),
        ("Sandwich Poulet Pané / Grillé", "🥪 Sandwiches & Savory Snacks", 30.0),
        ("Sandwich Merguez", "🥪 Sandwiches & Savory Snacks", 30.0),
        ("Msemen Farcie", "🥪 Sandwiches & Savory Snacks", 22.0),
        ("Harcha Farcie", "🥪 Sandwiches & Savory Snacks", 18.0),
        ("Msemen (Plain)", "🥐 Moroccan Pastries & Baked Goods", 8.0),
        ("Harcha (Plain)", "🥐 Moroccan Pastries & Baked Goods", 8.0),
        ("Baghrir", "🥐 Moroccan Pastries & Baked Goods", 8.0),
        ("Croissants & Pain au Chocolat", "🥐 Moroccan Pastries & Baked Goods", 10.0),
        ("Thé à la Menthe (Moroccan Mint Tea)", "🍵 Hot Beverages", 10.0),
        ("Thé à la Louiza", "🍵 Hot Beverages", 10.0),
        ("Café au Lait", "🍵 Hot Beverages", 12.0),
        ("Café Noir", "🍵 Hot Beverages", 10.0),
        ("Jus d'Avocat au Lait", "🥤 Cold Drinks & Fresh Juices", 22.0),
        ("Jus d'Orange", "🥤 Cold Drinks & Fresh Juices", 15.0),
        ("Jus Panaché", "🥤 Cold Drinks & Fresh Juices", 20.0),
        ("Rayeb (Lben)", "🥤 Cold Drinks & Fresh Juices", 12.0),
        ("Mineral Water & Soft Drinks", "🥤 Cold Drinks & Fresh Juices", 10.0),
        ("Harira", "🍲 Soups & Warm Dishes (Seasonal/Daily)", 18.0),
        ("Bissara", "🍲 Soups & Warm Dishes (Seasonal/Daily)", 15.0),
    ]

    inventory = load_inventory()
    products_by_name = {product.nom: product for product in inventory}

    for nom, categorie, prix in menu_items:
        if nom in products_by_name:
            existing = products_by_name[nom]
            existing.categorie = categorie
            existing.prix = prix
        else:
            products_by_name[nom] = Produit(
                id=max((product.id for product in inventory), default=0) + 1,
                nom=nom,
                categorie=categorie,
                prix=prix,
                stock_actuel=50,
                seuil_alerte=5,
            )
            inventory.append(products_by_name[nom])

    save_inventory(inventory)
    print(f"Menu products synchronized: {len(menu_items)}")


if __name__ == "__main__":
    seed_produits()