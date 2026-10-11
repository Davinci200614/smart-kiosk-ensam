class Produit:
    def __init__(
        self, id, nom, categorie, prix, stock_actuel, seuil_alerte, image_path=None
    ):
        self.id = id
        self.nom = nom
        self.categorie = categorie
        self.prix = prix
        self.stock_actuel = stock_actuel
        self.seuil_alerte = seuil_alerte
        self.image_path = image_path

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "categorie": self.categorie,
            "prix": self.prix,
            "stock_actuel": self.stock_actuel,
            "seuil_alerte": self.seuil_alerte,
            "image_path": self.image_path
        }
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            nom=data["nom"],
            categorie=data["categorie"],
            prix=data["prix"],
            stock_actuel=data["stock_actuel"],
            seuil_alerte=data["seuil_alerte"],
            image_path=data["image_path"]
        )
class Commande:
    def __init__(
        self,
        id,
        date_heure,
        statut="En attente",
        total=0.0,
        mode_paiement=None,
        qr_code_path=None,
    ):
        self.id = id
        self.date_heure = date_heure
        self.statut = statut
        self.total = total
        self.mode_paiement = mode_paiement
        self.qr_code_path = qr_code_path

    def to_dict(self):
        return {
            "id": self.id,
            "date_heure": self.date_heure,
            "statut": self.statut,
            "total": self.total,
            "mode_paiement": self.mode_paiement,
            "qr_code_path": self.qr_code_path,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            date_heure=data["date_heure"],
            statut=data.get("statut", "En attente"),
            total=data.get("total", 0.0),
            mode_paiement=data.get("mode_paiement"),
            qr_code_path=data.get("qr_code_path"),
        )
class LigneCommande:
    def __init__(self, id, commande_id, produit_id, quantite, prix_unitaire):
        self.id = id
        self.commande_id = commande_id
        self.produit_id = produit_id
        self.quantite = quantite
        self.prix_unitaire = prix_unitaire

    def to_dict(self):
        return {
            "id": self.id,
            "commande_id": self.commande_id,
            "produit_id": self.produit_id,
            "quantite": self.quantite,
            "prix_unitaire": self.prix_unitaire
        }
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            commande_id=data["commande_id"],
            produit_id=data["produit_id"],
            quantite=data["quantite"],
            prix_unitaire=data["prix_unitaire"]
        )
class Utilisateur:
    def __init__(self, id, nom_utilisateur, mot_de_passe_hash, role):
        self.id = id
        self.nom_utilisateur = nom_utilisateur
        self.mot_de_passe_hash = mot_de_passe_hash
        self.role = role

    def to_dict(self):
        return {
            "id": self.id,
            "nom_utilisateur": self.nom_utilisateur,
            "mot_de_passe_hash": self.mot_de_passe_hash,
            "role": self.role
        }
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            nom_utilisateur=data["nom_utilisateur"],
            mot_de_passe_hash=data["mot_de_passe_hash"],
            role=data["role"]
        )