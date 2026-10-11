import json
from datetime import datetime
from backend.models_json import Commande, LigneCommande, Produit, Utilisateur
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
inventory_file = DATA_DIR / "inventory.json"
transactions_file = DATA_DIR / "transactions.json"
users_file = DATA_DIR / "user.json"
refill_requests_file = DATA_DIR / "refill_requests.json"


def _read_json(path, default):
    if not path.exists() or path.stat().st_size == 0:
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_inventory():
    return [Produit.from_dict(item) for item in _read_json(inventory_file, [])]

def load_transactions():
    raw_data = _read_json(transactions_file, {"commandes": [], "lignes": []})
    commandes = [Commande.from_dict(item) for item in raw_data.get("commandes", [])]
    lignes = [LigneCommande.from_dict(item) for item in raw_data.get("lignes", [])]
    return commandes, lignes

def load_users():
    return [Utilisateur.from_dict(item) for item in _read_json(users_file, [])]


def save_inventory(inventory):
    _write_json(inventory_file, [product.to_dict() for product in inventory])


def save_transactions(commandes, lignes):
    _write_json(
        transactions_file,
        {
            "commandes": [commande.to_dict() for commande in commandes],
            "lignes": [ligne.to_dict() for ligne in lignes],
        },
    )


def save_users(users):
    _write_json(users_file, [user.to_dict() for user in users])


def load_refill_requests():
    """Load persisted stock refill requests."""
    return _read_json(refill_requests_file, [])


def save_refill_requests(requests):
    """Persist stock refill requests as a JSON list."""
    _write_json(refill_requests_file, requests)


def create_commande(panier, mode_paiement="Espèces"):
    """Create an order, its lines, and update inventory in one JSON write cycle."""
    if not panier:
        return None

    inventory = load_inventory()
    commandes, lignes = load_transactions()
    products_by_id = {product.id: product for product in inventory}
    quantities = {}

    for product in panier:
        quantities[product.id] = quantities.get(product.id, 0) + 1

    for product_id, quantity in quantities.items():
        product = products_by_id.get(product_id)
        if product is None:
            raise ValueError(f"Produit inconnu: {product_id}")
        if product.stock_actuel < quantity:
            raise ValueError(f"Stock insuffisant pour: {product.nom}")

    order_id = max((order.id for order in commandes), default=0) + 1
    line_id = max((line.id for line in lignes), default=0) + 1
    order = Commande(
        id=order_id,
        date_heure=datetime.now().isoformat(timespec="seconds"),
        statut="En attente",
        total=sum(products_by_id[product_id].prix * quantity for product_id, quantity in quantities.items()),
        mode_paiement=mode_paiement,
    )

    new_lines = []
    for product_id, quantity in quantities.items():
        product = products_by_id[product_id]
        product.stock_actuel -= quantity
        new_lines.append(
            LigneCommande(
                id=line_id,
                commande_id=order.id,
                produit_id=product.id,
                quantite=quantity,
                prix_unitaire=product.prix,
            )
        )
        line_id += 1

    save_inventory(inventory)
    save_transactions(commandes + [order], lignes + new_lines)
    return order

def new_func():
    inventory = load_inventory()
    return inventory


def get_active_commandes():
    """Return active orders with their lines and product names."""
    commandes, lignes = load_transactions()
    inventory = {product.id: product for product in load_inventory()}
    active = []
    for commande in commandes:
        if commande.statut != "Servie":
            order_lines = [
                (line, inventory.get(line.produit_id))
                for line in lignes
                if line.commande_id == commande.id
            ]
            active.append((commande, order_lines))
    return active


def update_commande_status(order_id, current_status):
    commandes, lignes = load_transactions()
    next_status = {
        "En attente": "En préparation",
        "En préparation": "Servie",
    }.get(current_status)
    if next_status is None:
        return False

    for commande in commandes:
        if commande.id == order_id:
            commande.statut = next_status
            save_transactions(commandes, lignes)
            return True
    return False