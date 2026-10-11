from backend.models_json import Produit
from backend.storage_json import load_inventory, save_inventory

def seed_produits():
    inventory = load_inventory()
    if inventory:
        print("JSON inventory already contains products. Skipping seed.")
        return

    menu_items = [
        Produit(1, "Café Noir", "Boissons", 5.0, 50, 10),
        Produit(2, "Thé à la Menthe", "Boissons", 3.0, 100, 20),
        Produit(3, "Panini Poulet", "Sandwichs", 25.0, 20, 5),
        Produit(4, "Tacos Viande Hachée", "Sandwichs", 30.0, 15, 5),
        Produit(5, "Chips Lays", "Snacks", 10.0, 40, 10),
        Produit(6, "Tarte au Citron", "Desserts", 12.0, 10, 3),
    ]

    save_inventory(menu_items)
    print(f"Successfully added {len(menu_items)} products to inventory.json.")

if __name__ == "__main__":
    seed_produits()