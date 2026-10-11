import os
import qrcode
from sqlalchemy.orm import Session
from backend.models import Commande, LigneCommande, Produit
from sqlalchemy.orm import joinedload

ORDER_STATUSES = ("En attente", "En préparation", "Prête", "Servie")

# Ensure a directory exists to store the generated tickets
if not os.path.exists("qrcodes"):
    os.makedirs("qrcodes")

def get_produits(db: Session) -> list[Produit]:
    return db.query(Produit).order_by(Produit.categorie, Produit.nom).all()


def get_commandes(db: Session, include_served: bool = True) -> list[Commande]:
    query = db.query(Commande).options(
        joinedload(Commande.lignes).joinedload(LigneCommande.produit)
    )
    if not include_served:
        query = query.filter(Commande.statut != "Servie")
    return query.order_by(Commande.date_heure.desc(), Commande.id.desc()).all()


def update_commande_status(
    db: Session, commande_id: int, statut: str
) -> Commande | None:
    if statut not in ORDER_STATUSES:
        raise ValueError(f"Statut de commande invalide: {statut}")

    commande = db.query(Commande).filter(Commande.id == commande_id).first()
    if commande is None:
        return None

    commande.statut = statut
    db.commit()
    db.refresh(commande)
    return commande


def create_commande(db: Session, panier: list, mode_paiement: str = "Espèces"):
    if not panier:
        print("Le panier est vide.")
        return None

    try:
        # 1. Group items by ID
        lignes_data = {}
        for item in panier:
            if item.id in lignes_data:
                lignes_data[item.id]['quantite'] += 1
            else:
                lignes_data[item.id] = {'produit': item, 'quantite': 1}

        produits = {}
        total_commande = 0.0
        for prod_id, data in lignes_data.items():
            db_produit = db.query(Produit).filter(Produit.id == prod_id).first()
            if db_produit is None:
                raise ValueError(f"Produit introuvable: {prod_id}")
            if db_produit.stock_actuel < data['quantite']:
                raise ValueError(f"Stock insuffisant: {db_produit.nom}")
            produits[prod_id] = db_produit
            total_commande += db_produit.prix * data['quantite']

        # 2. Create the parent order
        nouvelle_commande = Commande(
            total=total_commande,
            mode_paiement=mode_paiement,
            statut="En attente"
        )
        db.add(nouvelle_commande)
        db.flush() 

        # 3. Create lines and decrement stock
        for prod_id, data in lignes_data.items():
            qte = data['quantite']
            db_produit = produits[prod_id]
            db_produit.stock_actuel -= qte
            nouvelle_ligne = LigneCommande(
                commande_id=nouvelle_commande.id,
                produit_id=prod_id,
                quantite=qte,
                prix_unitaire=db_produit.prix
            )
            db.add(nouvelle_ligne)

        # 4. Generate the ticket before committing the order and stock changes.
        db.flush()
        
        # 5. Generate and save the QR Code
        qr_data = f"ENSAM Buvette\nCommande: #{nouvelle_commande.id}\nTotal: {total_commande} DH\nStatut: {nouvelle_commande.statut}"
        qr = qrcode.make(qr_data)
        
        qr_filename = f"qrcodes/ticket_cmd_{nouvelle_commande.id}.png"
        qr.save(qr_filename)
        
        # 5. Commit the order, ticket path, and stock changes together.
        nouvelle_commande.qr_code_path = qr_filename
        db.commit()
        db.refresh(nouvelle_commande)

        print(f"Succès: Commande #{nouvelle_commande.id} enregistrée. Ticket généré: {qr_filename}")
        return nouvelle_commande

    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la transaction: {e}")
        return None