from backend.database import SessionLocal, init_db
from backend.models import Produit

def seed_produits():
    # Ensure tables exist before injecting data
    init_db()
    
    # Open a database session
    db = SessionLocal()
    
    # Check if the database is already populated to avoid duplicates
    if db.query(Produit).count() > 0:
        print("Database already contains products. Skipping seed.")
        db.close()
        return

    # Define mock buvette items
    menu_items = [
        Produit(nom="Café Noir", categorie="Boissons", prix=5.0, stock_actuel=50, seuil_alerte=10),
        Produit(nom="Thé à la Menthe", categorie="Boissons", prix=3.0, stock_actuel=100, seuil_alerte=20),
        Produit(nom="Panini Poulet", categorie="Sandwichs", prix=25.0, stock_actuel=20, seuil_alerte=5),
        Produit(nom="Tacos Viande Hachée", categorie="Sandwichs", prix=30.0, stock_actuel=15, seuil_alerte=5),
        Produit(nom="Chips Lays", categorie="Snacks", prix=10.0, stock_actuel=40, seuil_alerte=10),
        Produit(nom="Tarte au Citron", categorie="Desserts", prix=12.0, stock_actuel=10, seuil_alerte=3)
    ]

    # Add all items to the staging area and commit to the SQLite file
    db.add_all(menu_items)
    db.commit()
    print(f"Successfully added {len(menu_items)} products to the database.")
    
    db.close()

if __name__ == "__main__":
    seed_produits()