"""JSON-backed order and inventory operations.

This module preserves the historical CRUD API expected by the UI while operating
on the JSON files in backend/ instead of SQLite/SQLAlchemy.
"""

from __future__ import annotations

import os
from datetime import datetime

import qrcode

from backend.models_json import Commande, LigneCommande, Produit
from backend.storage_json import (
    load_inventory,
    load_transactions,
    save_inventory,
    save_transactions,
)

ORDER_STATUSES = ("En attente", "En préparation", "Prête", "Servie")

# Ensure a directory exists to store the generated tickets.
if not os.path.exists("qrcodes"):
    os.makedirs("qrcodes")


def get_produits(db: object | None = None) -> list[Produit]:
    """Return the current inventory from the JSON persistence layer."""
    return load_inventory()


def get_commandes(db: object | None = None, include_served: bool = True) -> list[Commande]:
    """Return all commands with their lines and product references attached."""
    commandes, lignes = load_transactions()
    produits = {produit.id: produit for produit in load_inventory()}

    visible: list[Commande] = []
    for commande in commandes:
        if not include_served and commande.statut == "Servie":
            continue

        commande.lignes = []
        for ligne in lignes:
            if ligne.commande_id == commande.id:
                ligne.produit = produits.get(ligne.produit_id)
                commande.lignes.append(ligne)

        visible.append(commande)

    visible.sort(key=lambda item: (item.date_heure, item.id), reverse=True)
    return visible


def update_commande_status(
    db: object | None,
    commande_id: int,
    statut: str,
) -> Commande | None:
    """Update an order status in the JSON storage layer."""
    if statut not in ORDER_STATUSES:
        raise ValueError(f"Statut de commande invalide: {statut}")

    commandes, lignes = load_transactions()
    for commande in commandes:
        if commande.id != commande_id:
            continue
        commande.statut = statut
        save_transactions(commandes, lignes)
        commande.lignes = [ligne for ligne in lignes if ligne.commande_id == commande.id]
        return commande
    return None


def create_commande(db: object | None, panier: list, mode_paiement: str = "Espèces"):
    """Create a command in the JSON data store while updating stock.

    The function accepts the legacy database parameter so the Tkinter UI can call
    it without changes.
    """
    if not panier:
        print("Le panier est vide.")
        return None

    try:
        inventory = load_inventory()
        commandes, lignes = load_transactions()
        produits = {produit.id: produit for produit in inventory}
        grouped: dict[int, int] = {}

        for item in panier:
            grouped[item.id] = grouped.get(item.id, 0) + 1

        total_commande = 0.0
        for produit_id, quantity in grouped.items():
            produit = produits.get(produit_id)
            if produit is None:
                raise ValueError(f"Produit introuvable: {produit_id}")
            if produit.stock_actuel < quantity:
                raise ValueError(f"Stock insuffisant: {produit.nom}")
            total_commande += produit.prix * quantity

        next_order_id = max((commande.id for commande in commandes), default=0) + 1
        next_line_id = max((ligne.id for ligne in lignes), default=0) + 1

        nouvelle_commande = Commande(
            id=next_order_id,
            date_heure=datetime.now().isoformat(timespec="seconds"),
            statut="En attente",
            total=total_commande,
            mode_paiement=mode_paiement,
        )

        nouvelles_lignes: list[LigneCommande] = []
        for produit_id, quantity in grouped.items():
            produit = produits[produit_id]
            produit.stock_actuel -= quantity
            nouvelles_lignes.append(
                LigneCommande(
                    id=next_line_id,
                    commande_id=nouvelle_commande.id,
                    produit_id=produit.id,
                    quantite=quantity,
                    prix_unitaire=produit.prix,
                )
            )
            next_line_id += 1

        qr_data = (
            f"ENSAM Buvette\nCommande: #{nouvelle_commande.id}\n"
            f"Total: {total_commande} DH\nStatut: {nouvelle_commande.statut}"
        )
        qr = qrcode.make(qr_data)
        qr_filename = f"qrcodes/ticket_cmd_{nouvelle_commande.id}.png"
        qr.save(qr_filename)
        nouvelle_commande.qr_code_path = qr_filename

        save_inventory(inventory)
        save_transactions(commandes + [nouvelle_commande], lignes + nouvelles_lignes)

        nouvelle_commande.lignes = nouvelles_lignes
        for ligne in nouvelle_commande.lignes:
            ligne.produit = produits.get(ligne.produit_id)

        print(f"Succès: Commande #{nouvelle_commande.id} enregistrée. Ticket généré: {qr_filename}")
        return nouvelle_commande

    except Exception as exc:  # pragma: no cover - runtime error path
        print(f"Erreur lors de la transaction: {exc}")
        return None