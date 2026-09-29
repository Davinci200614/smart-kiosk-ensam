import os
import qrcode
from sqlalchemy.orm import Session
from backend.models import Commande, LigneCommande, Produit

# Ensure a directory exists to store the generated tickets
if not os.path.exists("qrcodes"):
    os.makedirs("qrcodes")

def create_commande(db: Session, panier: list, mode_paiement: str = "Espèces"):
    if not panier:
        print("Le panier est vide.")
        return None

    try:
        # 1. Group items by ID
        lignes_data = {}
        total_commande = 0.0
        
        for item in panier:
            total_commande += item.prix
            if item.id in lignes_data:
                lignes_data[item.id]['quantite'] += 1
            else:
                lignes_data[item.id] = {'produit': item, 'quantite': 1}

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
            db_produit = db.query(Produit).filter(Produit.id == prod_id).first()
            if db_produit:
                db_produit.stock_actuel -= qte
                nouvelle_ligne = LigneCommande(
                    commande_id=nouvelle_commande.id,
                    produit_id=prod_id,
                    quantite=qte,
                    prix_unitaire=db_produit.prix
                )
                db.add(nouvelle_ligne)

        # 4. Commit the initial transaction to lock in the ID
        db.commit()
        db.refresh(nouvelle_commande)
        
        # 5. Generate and save the QR Code
        qr_data = f"ENSAM Buvette\nCommande: #{nouvelle_commande.id}\nTotal: {total_commande} DH\nStatut: {nouvelle_commande.statut}"
        qr = qrcode.make(qr_data)
        
        qr_filename = f"qrcodes/ticket_cmd_{nouvelle_commande.id}.png"
        qr.save(qr_filename)
        
        # 6. Update the order with the image path and commit again
        nouvelle_commande.qr_code_path = qr_filename
        db.commit()

        print(f"Succès: Commande #{nouvelle_commande.id} enregistrée. Ticket généré: {qr_filename}")
        return nouvelle_commande

    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la transaction: {e}")
        return None