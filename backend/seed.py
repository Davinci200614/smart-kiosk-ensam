"""Seed the JSON inventory for the kiosk menu."""

from __future__ import annotations

from backend.models_json import Produit
from backend.storage_json import load_inventory, save_inventory


MENU_ITEMS = (
    ("Sandwich Bocadillos", "🍽️ Plats", 28.0),
    ("Sandwich Kefta", "🍽️ Plats", 32.0),
    ("Sandwich Poulet Pané / Grillé", "🍽️ Plats", 30.0),
    ("Sandwich Merguez", "🍽️ Plats", 30.0),
    ("Msemen Farcie", "🍽️ Plats", 22.0),
    ("Harcha Farcie", "🍽️ Plats", 18.0),
    ("Msemen (Plain)", "🍰 Pâtisseries", 8.0),
    ("Harcha (Plain)", "🍰 Pâtisseries", 8.0),
    ("Baghrir", "🍰 Pâtisseries", 8.0),
    ("Croissants & Pain au Chocolat", "🍰 Pâtisseries", 10.0),
    ("Thé à la Menthe (Moroccan Mint Tea)", "🥤 Boissons", 10.0),
    ("Thé à la Louiza", "🥤 Boissons", 10.0),
    ("Café au Lait", "🥤 Boissons", 12.0),
    ("Café Noir", "🥤 Boissons", 10.0),
    ("Jus d'Avocat au Lait", "🥤 Boissons", 22.0),
    ("Jus d'Orange", "🥤 Boissons", 15.0),
    ("Jus Panaché", "🥤 Boissons", 20.0),
    ("Rayeb (Lben)", "🥤 Boissons", 12.0),
    ("Mineral Water & Soft Drinks", "🥤 Boissons", 10.0),
    ("Harira", "🍽️ Plats", 18.0),
    ("Bissara", "🍽️ Plats", 15.0),
)


def seed_produits() -> None:
    """Populate JSON inventory with the default menu if needed."""
    inventory = load_inventory()
    menu_names = {name for name, _, _ in MENU_ITEMS}
    inventory = [product for product in inventory if product.nom in menu_names]
    products_by_name = {product.nom: product for product in inventory}

    for nom, categorie, prix in MENU_ITEMS:
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
    print(f"Menu products synchronized: {len(MENU_ITEMS)}")


if __name__ == "__main__":
    seed_produits()