# Smart Kiosk & Management System — Buvette ENSAM

Application Python simulant une **borne de commande interactive** (type McDonald's) couplée à un **système de caisse / suivi cuisine** et à un **module d'analyse financière** pour les gérants de la buvette de l'ENSAM.



| **Langage** | Python 3.10+ |


---

## 1. Contexte et objectifs

La buvette de l'ENSAM fait face à une forte affluence lors des pauses, ce qui génère de longues files d'attente et une gestion complexe des stocks et de la caisse.

Ce projet vise à concevoir une application complète permettant :

- aux clients de commander eux-mêmes via une borne tactile ;
- au personnel de suivre et servir les commandes en direct ;
- aux gérants de piloter les stocks et d'analyser le chiffre d'affaires.

## 2. Architecture

```
┌─────────────────────┐      ┌──────────────────────────┐
│  Borne Client       │      │  Caisse & Cuisine        │
│  (Kiosk UI)         │      │  (Manager UI / KDS)      │
└─────────┬───────────┘      └────────────┬─────────────┘
          │                               │
          └───────────┐   ┌───────────────┘
                      ▼   ▼
              ┌─────────────────┐       ┌──────────────────────┐
              │ Fichiers JSON   │◄──────│ Analytics & Rapports │
              │ (storage_json)  │       │ (Streamlit / Plotly) │
              └─────────────────┘       └──────────────────────┘
```

### Arborescence cible

```
.
├── main.py                  # Point d'entrée (menu de lancement des modules)
├── requirements.txt
├── setup.sh                 # Installation et lancement en une commande
├── backend/
│   ├── models_json.py       # Modèles Python sérialisables en JSON
│   ├── storage_json.py      # Lecture/écriture des données JSON
│   ├── crud.py              # Création des commandes et tickets QR
│   ├── auth_json.py         # Authentification des managers
│   ├── seed.py              # Données initiales de l'inventaire
│   ├── inventory.json       # Produits et stocks
│   ├── transactions.json    # Commandes et lignes de commande
│   └── user.json            # Utilisateurs
├── frontend/
│   ├── kiosk_ui.py          # Borne client
│   └── manager_ui.py        # Caisse & suivi cuisine
├── analytics/
│   └── dashboard.py         # Dashboard financier + exports
├── assets/                  # Images produits
└── qrcodes/                 # Tickets générés
```

## 3. Modules fonctionnels

### 3.1 Module 1 — Borne client (Kiosk)

- **Catalogue interactif** : navigation par catégories (*Boissons, Snacks, Sandwichs, Desserts*) avec affichage des images et des prix.
- **Panier dynamique** : ajout, ajustement des quantités et suppression d'articles, avec calcul du total en temps réel.
- **Passage de commande** : choix du mode de paiement (*Espèces au guichet*, *Carte / Solde étudiant*) puis validation.
- **Génération du billet** : affichage d'un numéro de commande clair et d'un **QR Code unique** pour le retrait.

### 3.2 Module 2 — Interface Caisse & Suivi Cuisine (KDS)

- **Suivi en direct** : affichage automatique des nouvelles commandes avec changement de statut :
  `En attente → En préparation → Prête → Servie`
- **Scan / Validation** : validation des commandes servies via leur numéro ou par scan du QR Code.
- **Gestion du stock** : décrémentation automatique après achat et **alertes visuelles** lorsque le seuil critique est atteint.

### 3.3 Module 3 — Analytics & Rapports financiers

- **Tableau de bord** : chiffre d'affaires par jour / par heure, analyse des périodes de pointe, produits les plus vendus.
- **Exportation** : génération automatique de bilans financiers en **PDF** et **CSV**.

## 4. Stack technologique

| Composant | Technologie | Rôle |
|---|---|---|
| Langage | Python 3.10+ | Cœur du projet |
| Interface graphique | CustomTkinter | Borne client, caisse et suivi cuisine |
| Dashboard analytics | Streamlit / Plotly | Visualisation fluide des données financières |
| Persistance | Fichiers JSON | Stockage local de l'inventaire, des commandes et des utilisateurs |
| QR Code | `qrcode` & `Pillow` | Création des QR Codes des tickets |
| Analyse de données | `pandas` | Traitement et agrégation des données financières |

## 5. Fichiers de données JSON

| Fichier | Contenu |
|---|---|
| `inventory.json` | Produits, catégories, prix, stock et seuils d'alerte |
| `transactions.json` | Commandes et lignes de commande |
| `user.json` | Utilisateurs managers et mots de passe hachés |
| `refill_requests.json` | Demandes de réapprovisionnement |

Les modèles de [`backend/models_json.py`](backend/models_json.py) sont convertis
en dictionnaires avant d'être écrits par [`backend/storage_json.py`](backend/storage_json.py).
Les tickets QR sont générés dans `qrcodes/` à la racine du projet.

## 6. Installation et lancement

```bash

# Préparer l'environnement, initialiser les données JSON et ouvrir le lanceur
chmod +x setup.sh
./setup.sh

# Ou lancer directement une interface (la venv est utilisée automatiquement)
./setup.sh kiosk                 # Borne client
./setup.sh manager               # Caisse & suivi cuisine
./setup.sh dashboard             # Dashboard financier
```

`setup.sh` crée `venv/` si nécessaire, installe les dépendances, initialise
`backend/inventory.json`, puis exécute `main.py` avec l'interpréteur de la
machine virtuelle. Il n'est donc pas nécessaire d'activer la venv séparément.

### Dépendances (`requirements.txt`)

```
customtkinter
qrcode
pillow
pandas
plotly
streamlit
```

## 7. Répartition des tâches

| Membre | Rôle | Sem. 1 | Sem. 2 | Sem. 3 |
|---|---|---|---|---|
| **1** | Frontend client (borne tactile) | Maquettage UI/UX, catalogue interactif | Panier dynamique, quantités, récapitulatif | Confirmation, QR Code, intégration JSON |
| **2** | Backend, données & logique métier | Modèles JSON, données initiales | CRUD, stocks, commandes, transactions | Synchronisation borne-caisse, erreurs, cas limites |
| **3** | Caisse, cuisine & module financier | Écran Suivi Cuisine, statuts | Administration des stocks, seuils d'alerte | Dashboard financier, pandas/Plotly, rapports |

## 8. Planning prévisionnel

| Période | Objectifs |
|---|---|
| **Semaine 1** | Modèles JSON, maquettes UI Borne & Caisse, structure du projet |
| **Semaine 2** | Connexion Borne-inventaire JSON, décrémentation du stock, écran Suivi Cuisine |
| **Semaine 3** | Dashboard financier, génération QR/PDF, tests d'intégration, soutenance |

### Jalons de livraison

1. **Fin semaine 1** : stockage JSON fonctionnel et maquettes UI validées.
2. **Fin semaine 2** : parcours de commande complet (de la sélection au suivi en cuisine).
3. **Fin semaine 3** : projet finalisé et testé, tableaux de bord et support de présentation prêts.

## 9. État d'avancement (prototype actuel)

Légende : ✅ fait · 🟡 partiel · ❌ à faire

### Base de données et backend

| Exigence | État | Remarque |
|---|---|---|
| Modèles et stockage JSON | ✅ | Inventaire, transactions, utilisateurs et demandes de réapprovisionnement |
| Données initiales (seed) | ✅ | Inventaire initial chargé dans `inventory.json` |
| Création de commande | ✅ | Lignes, total et persistance dans `transactions.json` |
| Décrémentation automatique du stock | ✅ | Vérification du stock disponible avant l'écriture |
| Génération du QR Code | ✅ | Ticket enregistré dans `qrcodes/` et chemin sauvegardé |
| Gestion des utilisateurs (Admin / Caissier) | ✅ | Authentification JSON des managers |
| Gestion des erreurs et cas limites | 🟡 | Erreurs métier gérées, couverture de tests à renforcer |

### Module 1 — Borne client

| Exigence | État | Remarque |
|---|---|---|
| Navigation par catégories | ❌ | Liste unique de boutons |
| Affichage des images produits | ❌ | `image_path` jamais utilisé |
| Ajout au panier + total en temps réel | ✅ | |
| Ajustement des quantités / suppression | ❌ | Ajout uniquement |
| Choix du mode de paiement | ❌ | « Espèces » codé en dur |
| Numéro de commande + QR Code affichés | ❌ | Numéro visible 3 s sur le bouton, pas de ticket |

### Module 2 — Caisse & Cuisine (KDS)

| Exigence | État | Remarque |
|---|---|---|
| Affichage automatique des commandes | ✅ | Rafraîchissement toutes les 5 s, sans scintillement |
| Statuts En attente / En préparation / Servie | ✅ | |
| Statut « Prête » | ❌ | Passage direct de *En préparation* à *Servie* |
| Validation par numéro ou scan QR | ❌ | |
| Administration des stocks | ❌ | Aucune interface |
| Alertes visuelles sur seuil critique | ❌ | `seuil_alerte` jamais exploité |

### Module 3 — Analytics

| Exigence | État | Remarque |
|---|---|---|
| Dashboard (CA par jour/heure, pointes, top produits) | 🟡 | Dashboard Streamlit connecté aux transactions JSON |
| Export PDF / CSV | ❌ | |

### Projet

| Exigence | État | Remarque |
|---|---|---|
| `requirements.txt` | ✅ | Dépendances de l'application déclarées |
| `main.py` | ✅ | Lanceur graphique et lancement direct des interfaces |
| `setup.sh` | ✅ | Installation, seed JSON et lancement en une commande |
| Tests d'intégration | ❌ | |

## 10. Pistes d'amélioration identifiées

- Retirer `*.png` et `*.pdf` du `.gitignore` pour ne pas exclure les images produits (ou ignorer uniquement `qrcodes/`).
- Remplacer le contenu du QR Code (statut figé à la création) par un identifiant exploitable au scan, par exemple `ENSAM-CMD-<id>`.
- Remplacer `datetime.utcnow` par un horodatage timezone-aware (heure du Maroc) pour des statistiques horaires correctes.
- Supprimer le contournement `self.panier.append(None)` dans `KioskApp.checkout`.
- Utiliser les prix de la base (et non ceux du panier en mémoire) pour calculer le total dans `create_commande`.

## 11. Livrables attendus

- Application fonctionnelle (borne, caisse/cuisine, dashboard).
- Bilans financiers exportables (PDF et CSV).
- Support de présentation pour la soutenance.
