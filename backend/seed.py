from backend.database import SessionLocal, init_db
from backend.models import Produit

def seed_produits():
    init_db()
    db = SessionLocal()
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

    try:
        for nom, categorie, prix in menu_items:
            produit = db.query(Produit).filter(Produit.nom == nom).first()
            if produit is None:
                produit = Produit(
                    nom=nom,
                    categorie=categorie,
                    prix=prix,
                    stock_actuel=50,
                    seuil_alerte=5,
                )
                db.add(produit)
            else:
                produit.categorie = categorie
                produit.prix = prix

        db.commit()
        print(f"Menu products synchronized: {len(menu_items)}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_produits()