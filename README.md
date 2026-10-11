# Smart Kiosk & Management System — Buvette ENSAM

Application Python pour gérer une borne de commande autonome, le suivi des commandes côté cuisine/caisse et un tableau de bord financier pour la buvette de l'ENSAM.

Le projet combine :
- une interface client tactile,
- un écran gestionnaire pour la cuisine et la caisse,
- un moteur de persistance basé sur des fichiers JSON,
- un tableau de bord analytique avec Streamlit.

## Objectif

La buvette accueille de nombreux clients pendant les pauses. Le projet vise à réduire les files d'attente, centraliser la gestion des commandes et offrir un suivi rapide des ventes et des stocks.

## Stack technique

- Python 3
- CustomTkinter pour les interfaces graphiques
- Streamlit + Plotly pour le dashboard
- JSON comme stockage local
- qrcode + Pillow pour les tickets QR
- pandas pour le traitement des données

## Structure du projet

```text
.
├── main.py                  # Point d'entrée principal
├── setup.sh                 # Script d'installation et de lancement
├── run.sh                   # Variante locale de lancement
├── requirements.txt         # Dépendances Python
├── backend/
│   ├── __init__.py
│   ├── auth_json.py         # Authentification manager
│   ├── crud.py              # Logique de commande et gestion des transactions
│   ├── inventory.json       # Stock du catalogue
│   ├── models_json.py       # Modèles de données
│   ├── refill_requests.json # Demandes de réapprovisionnement
│   ├── seed.py              # Initialisation du menu par défaut
│   ├── storage_json.py      # Lecture/écriture JSON
│   ├── transactions.json    # Historique des commandes
│   └── user.json            # Utilisateurs et accès
├── frontend/
│   ├── __init__.py
│   ├── kiosk.py             # Interface borne client
│   ├── kds.py               # Interface caisse / cuisine
│   └── moroccan_buvette_menu.md
├── analytics/
│   └── dashboard.py         # Tableau de bord financier
├── venv/                    # Environnement virtuel local
├── .gitignore
└── README.md
```

## Fonctionnalités

### 1. Borne client
- navigation dans les catégories de produits,
- ajout et suppression d'articles dans le panier,
- calcul du total en temps réel,
- sélection du mode de paiement,
- confirmation de commande et génération de ticket.

### 2. Gestion caisse / cuisine
- affichage des commandes en cours,
- suivi des statuts de commande,
- gestion des stocks après validation,
- vue adaptée au personnel de cuisine et de caisse.

### 3. Dashboard analytique
- visualisation du chiffre d'affaires,
- analyse des ventes par période,
- suivi des produits les plus demandés,
- export et consultation des données via Streamlit.

## Démarrage rapide

### Option 1 : script d'installation automatique

```bash
chmod +x setup.sh
./setup.sh
```

Le script :
1. crée un environnement virtuel local dans `venv/`,
2. installe les dépendances du projet,
3. initialise les fichiers JSON,
4. lance l'application.

### Option 2 : lancement manuel

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Lancement direct d'une interface

```bash
python main.py kiosk
python main.py manager
python main.py dashboard
```

## Fichiers de données

Les données de l'application sont stockées localement dans le dossier `backend` :

- `inventory.json` : catalogue, prix, stock et seuils
- `transactions.json` : commandes et détails
- `user.json` : comptes et accès manager
- `refill_requests.json` : demandes de réapprovisionnement

## Dépendances

```bash
customtkinter
qrcode
pillow
pandas
plotly
streamlit
```

## État du projet

Le projet est un prototype fonctionnel en cours de développement. Les blocs principaux sont en place : initialisation du menu, génération de commandes, stockage des données, lancement des interfaces, et dashboard analytique. Certaines fonctionnalités peuvent encore être améliorées et complétées selon les besoins du projet.

## Prochaines améliorations possibles

- améliorer le flux complet de paiement et la validation client,
- finaliser la gestion de l'état des commandes,
- renforcer les alertes sur les seuils de stock,
- enrichir les rapports financiers et les exports,
- nettoyer et stabiliser les interactions UI.

## Contribution

Ce projet est conçu pour servir de base de démonstration et de prototype de système de buvette intelligente. Les contributions sont bienvenues pour améliorer le parcours client, la logique métier et le tableau de bord analytique.
