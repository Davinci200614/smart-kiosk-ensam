from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
import sqlalchemy.orm
from datetime import datetime

Base = sqlalchemy.orm.declarative_base()

class Produit(Base):
    __tablename__ = 'produit'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String, nullable=False)
    categorie = Column(String, nullable=False) # e.g., 'Boissons', 'Snacks'
    prix = Column(Float, nullable=False)
    stock_actuel = Column(Integer, nullable=False, default=0)
    seuil_alerte = Column(Integer, nullable=False, default=5)
    image_path = Column(String, nullable=True)

class Commande(Base):
    __tablename__ = 'commande'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date_heure = Column(DateTime, default=datetime.utcnow)
    statut = Column(String, default="En attente") # En attente, En préparation, Prête, Servie
    total = Column(Float, nullable=False, default=0.0)
    mode_paiement = Column(String, nullable=True) # Espèces, Carte, Solde étudiant
    qr_code_path = Column(String, nullable=True)
    
    # Bidirectional relationship to LigneCommande
    lignes = sqlalchemy.orm.relationship("LigneCommande", back_populates="commande", cascade="all, delete-orphan")

class LigneCommande(Base):
    __tablename__ = 'ligne_commande'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    commande_id = Column(Integer, ForeignKey('commande.id'), nullable=False)
    produit_id = Column(Integer, ForeignKey('produit.id'), nullable=False)
    quantite = Column(Integer, nullable=False)
    prix_unitaire = Column(Float, nullable=False)
    
    # Relationships
    commande = sqlalchemy.orm.relationship("Commande", back_populates="lignes")
    produit = sqlalchemy.orm.relationship("Produit")

class Utilisateur(Base):
    __tablename__ = 'utilisateur'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nom_utilisateur = Column(String, unique=True, nullable=False)
    mot_de_passe_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'Admin' or 'Caissier'