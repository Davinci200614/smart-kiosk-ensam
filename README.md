# Smart Kiosk & Management System — Buvette ENSAM

Application Python simulant une **borne de commande interactive** (type McDonald's) couplée à un **système de caisse / suivi cuisine** et à un **module d'analyse financière** pour les gérants de la buvette de l'ENSAM.

| | |
|---|---|
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
              │ SQLite          │◄──────│ Analytics & Rapports │
              │ (SQLAlchemy)    │       │ (Streamlit / Plotly) │
              └─────────────────┘       └──────────────────────┘
```

### Arborescence cible

```
.
├── main.py                  # Point d'entrée (menu de lancement des modules)
├── requirements.txt
├── backend/
│   ├── models.py            # Modèles SQLAlchemy
│   ├── database.py          # Engine, session, init_db
│   ├── crud.py              # Logique métier (commandes, stocks, utilisateurs)
│   └── seed.py              # Données initiales
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
| Interface graphique | CustomTkinter ou Flet | Interface tactile moderne, responsive et sobre |
| Dashboard analytics | Streamlit / Plotly | Visualisation fluide des données financières |
| Base de données | SQLite + SQLAlchemy | ORM pour manipuler la base SQL locale |
| QR Code | `qrcode` & `Pillow` | Création des QR Codes des tickets |
| Rapports PDF | `reportlab` | Reçus et bilans comptables |
| Analyse de données | `pandas` & `matplotlib` | Traitement et agrégation des données financières |

## 5. Schéma de la base de données (SQLite)

| Table | Champs |
|---|---|
| **Produit** | `id`, `nom`, `categorie`, `prix`, `stock_actuel`, `seuil_alerte`, `image_path` |
| **Commande** | `id`, `date_heure`, `statut`, `total`, `mode_paiement`, `qr_code_path` |
| **LigneCommande** | `id`, `commande_id`, `produit_id`, `quantite`, `prix_unitaire` |
| **Utilisateur** | `id`, `nom_utilisateur`, `mot_de_passe_hash`, `role` (*Admin* / *Caissier*) |

Relations : `Commande 1—N LigneCommande N—1 Produit`.

## 6. Installation et lancement

```bash
# 1. Cloner le dépôt et créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Créer la base et injecter les données initiales
python -m backend.seed

# 4. Lancer les modules (depuis la racine du projet)
python -m frontend.kiosk_ui          # Borne client
python -m frontend.manager_ui        # Caisse & suivi cuisine
streamlit run analytics/dashboard.py # Dashboard financier
```

### Dépendances (`requirements.txt`)

```
customtkinter
sqlalchemy
qrcode
pillow
pandas
matplotlib
plotly
streamlit
reportlab
```

## 7. Répartition des tâches

| Membre | Rôle | Sem. 1 | Sem. 2 | Sem. 3 |
|---|---|---|---|---|
| **1** | Frontend client (borne tactile) | Maquettage UI/UX, catalogue interactif | Panier dynamique, quantités, récapitulatif | Confirmation, QR Code, intégration BDD |
| **2** | Backend, BDD & logique métier | Modélisation BDD, SQLAlchemy, données initiales | CRUD, stocks, commandes, transactions | Synchronisation borne-caisse, erreurs, cas limites |
| **3** | Caisse, cuisine & module financier | Écran Suivi Cuisine, statuts | Administration des stocks, seuils d'alerte | Dashboard financier, pandas/matplotlib, rapports PDF |

## 8. Planning prévisionnel

| Période | Objectifs |
|---|---|
| **Semaine 1** | Modélisation BDD, maquettes UI Borne & Caisse, structure du projet |
| **Semaine 2** | Connexion Borne-BDD, décrémentation du stock, écran Suivi Cuisine |
| **Semaine 3** | Dashboard financier, génération QR/PDF, tests d'intégration, soutenance |

### Jalons de livraison

1. **Fin semaine 1** : base de données fonctionnelle et maquettes UI validées.
2. **Fin semaine 2** : parcours de commande complet (de la sélection au suivi en cuisine).
3. **Fin semaine 3** : projet finalisé et testé, tableaux de bord et support de présentation prêts.

## 9. État d'avancement (prototype actuel)

Légende : ✅ fait · 🟡 partiel · ❌ à faire

### Base de données et backend

| Exigence | État | Remarque |
|---|---|---|
| Schéma des 4 tables | ✅ | Conforme au cahier des charges |
| Données initiales (seed) | ✅ | 6 produits, 4 catégories |
| Création de commande transactionnelle | ✅ | Lignes + total + rollback en cas d'erreur |
| Décrémentation automatique du stock | 🟡 | Fonctionne, mais aucune vérification du stock disponible (stock négatif possible) |
| Génération du QR Code | 🟡 | Image créée, mais jamais affichée au client |
| Gestion des utilisateurs (Admin / Caissier) | ❌ | Table présente, aucune authentification |
| Gestion des erreurs et cas limites | 🟡 | Seulement `print` + rollback |

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
| Dashboard (CA par jour/heure, pointes, top produits) | ❌ | `dashboard.py` vide |
| Export PDF / CSV | ❌ | |

### Projet

| Exigence | État | Remarque |
|---|---|---|
| `requirements.txt` | ❌ | Vide |
| `main.py` | ❌ | Vide |
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
