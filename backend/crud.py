from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import qrcode

from backend.models_json import Commande, Produit
from backend.storage_json import (
    create_commande as create_json_commande,
    load_transactions,
    save_transactions,
)

QR_CODES_DIR = Path(__file__).resolve().parent.parent / "qrcodes"


def create_commande(
    panier: Sequence[Produit],
    mode_paiement: str = "Espèces",
) -> Commande | None:
    """Create an order in the JSON database and generate its QR ticket.

    Inventory, orders, and order lines are persisted by ``storage_json``.
    The optional QR ticket path is then written back to the same JSON record.
    """
    order = create_json_commande(panier, mode_paiement)
    if order is None:
        return None

    QR_CODES_DIR.mkdir(parents=True, exist_ok=True)
    qr_filename = f"qrcodes/ticket_cmd_{order.id}.png"
    qr_path = QR_CODES_DIR / f"ticket_cmd_{order.id}.png"
    qr_data = (
        f"ENSAM Buvette\nCommande: #{order.id}\n"
        f"Total: {order.total} DH\nStatut: {order.statut}"
    )
    qrcode.make(qr_data).save(qr_path)

    commandes, lignes = load_transactions()
    saved_order = next(
        (commande for commande in commandes if commande.id == order.id),
        None,
    )
    if saved_order is None:
        raise RuntimeError(
            f"La commande #{order.id} est introuvable dans transactions.json."
        )

    saved_order.qr_code_path = qr_filename
    save_transactions(commandes, lignes)
    order.qr_code_path = qr_filename
    return order
