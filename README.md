# ShopFlow

[![ShopFlow CI](https://github.com/EagleFox31/shopflow/actions/workflows/ci.yml/badge.svg)](https://github.com/EagleFox31/shopflow/actions/workflows/ci.yml)

**Un backend de commerce multi-boutiques où un même compte peut posséder plusieurs boutiques, déléguer leur administration et gérer les catalogues, paniers, paiements ainsi que tout le cycle de vie des commandes.**

ShopFlow a été construit comme un projet pratique Python/FastAPI et a évolué d’un CRUD fortement centré sur les routers vers une architecture organisée autour d’une couche de services métier.

> **Tu apprends le backend ?** Commence par **[docs/START_HERE.md](docs/START_HERE.md)**. Le guide te donne les prérequis, l’ordre de lecture du code, les fichiers à étudier et des exercices progressifs pour comprendre ShopFlow sans te perdre dans l’architecture.

---

## Ce que modélise ShopFlow

Un utilisateur n’est pas limité à une seule boutique.

```mermaid
flowchart TD
    U[Utilisateur] --> S1[Boutique A]
    U --> S2[Boutique B]
    U --> S3[Boutique C]
    S1 --> P1[Produits]
    S1 --> C1[Paniers]
    S1 --> O1[Commandes]
    S2 --> P2[Produits]
    S2 --> O2[Commandes]
```

Le propriétaire d’une boutique peut également déléguer sa gestion à d’autres utilisateurs grâce aux permissions `ShopAdmin`. Les rôles globaux de la plateforme (`Role` / `UserRole`) restent séparés des permissions propres à chaque boutique.

## Architecture

```text
Requête HTTP
    ↓
Router FastAPI
    ├─ authentification / dépendances
    ├─ contrat de requête Pydantic
    └─ appel du service
           ↓
Service métier
    ├─ règles métier
    ├─ autorisation au niveau de la boutique
    ├─ orchestration
    └─ transitions d’état
           ↓
Session SQLAlchemy
           ↓
PostgreSQL
```

Le projet utilise volontairement **un fichier de service par domaine métier** :

```text
address_service      cart_service          cart_item_service
category_service     product_service       order_service
payment_service      shop_service          shop_admin_service
user_service         role_service          user_role_service
auth/token_service   shipment_service      notification_service
```

Cette architecture a remplacé l’approche initiale où une grande partie de la logique métier était directement placée dans les routers.

## Cycle de vie d’une commande

`order_service.py` joue le rôle d’orchestrateur central.

```mermaid
stateDiagram-v2
    [*] --> PENDING: panier → commande
    PENDING --> PAID: paiement réussi
    PAID --> CONFIRMED: confirmation boutique
    CONFIRMED --> SHIPPED: expédition créée
    SHIPPED --> DELIVERED: livraison confirmée
    DELIVERED --> RETURNED: retour client
    PENDING --> CANCELLED
    PAID --> CANCELLED
    CONFIRMED --> CANCELLED
```

Chaque transition est historisée dans `OrderStatusHistory`. Les données produit sont figées dans `OrderItem`, le stock est réservé lors de la création de la commande et il est restauré en cas d’annulation ou de retour.

## Diagrammes UML

### Diagramme de séquence — passage et traitement d’une commande

Ce diagramme montre le parcours principal depuis l’authentification du client jusqu’à la livraison d’une commande.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    actor Marchand
    participant API as API FastAPI
    participant Auth as AuthService
    participant Panier as CartService
    participant Produit as ProductService
    participant Commande as OrderService
    participant Paiement as PaymentService
    participant Livraison as ShipmentService
    participant DB as PostgreSQL

    Client->>API: POST /api/v1/auth/login
    API->>Auth: authentifier_utilisateur()
    Auth->>DB: vérifier email et mot de passe
    DB-->>Auth: utilisateur valide
    Auth-->>API: access token + refresh token
    API-->>Client: jetons JWT

    Client->>API: Ajouter un produit au panier
    API->>Panier: ajouter_article()
    Panier->>Produit: vérifier disponibilité et stock
    Produit->>DB: lire le produit dans la boutique
    DB-->>Produit: produit + stock
    Produit-->>Panier: disponible
    Panier->>DB: créer ou mettre à jour le panier
    DB-->>Panier: panier mis à jour
    Panier-->>API: panier courant
    API-->>Client: panier mis à jour

    Client->>API: POST /api/v1/shops/{shop_id}/orders
    API->>Commande: créer_commande_depuis_panier()
    Commande->>Panier: récupérer panier actif
    Panier->>DB: lire panier et articles
    DB-->>Panier: contenu du panier
    Panier-->>Commande: panier
    Commande->>Produit: réserver le stock
    Produit->>DB: décrémenter le stock
    DB-->>Produit: stock réservé
    Commande->>DB: créer Order, OrderItem et historique PENDING
    DB-->>Commande: commande créée
    Commande-->>API: commande
    API-->>Client: 201 Created

    Client->>API: Initier le paiement
    API->>Paiement: initier_paiement()
    Paiement->>DB: créer Payment PENDING
    DB-->>Paiement: paiement créé
    Paiement-->>API: paiement
    API-->>Client: paiement en attente

    Marchand->>API: Valider le paiement
    API->>Paiement: confirmer_paiement()
    Paiement->>DB: Payment → SUCCESS
    Paiement->>Commande: marquer_commande_payée()
    Commande->>DB: ajouter historique PAID
    DB-->>Commande: commande payée
    API-->>Marchand: paiement confirmé

    Marchand->>API: Confirmer la commande
    API->>Commande: confirmer_commande()
    Commande->>DB: statut CONFIRMED + historique
    DB-->>Commande: commande confirmée
    API-->>Marchand: commande confirmée

    Marchand->>API: Expédier la commande
    API->>Livraison: créer_expédition()
    Livraison->>DB: créer Shipment
    Livraison->>Commande: marquer_expédiée()
    Commande->>DB: statut SHIPPED + historique
    DB-->>Commande: commande expédiée
    API-->>Marchand: expédition créée

    Marchand->>API: Confirmer la livraison
    API->>Commande: livrer_commande()
    Commande->>DB: statut DELIVERED + historique
    DB-->>Commande: commande livrée
    API-->>Marchand: livraison confirmée
```

### Diagramme de classes — modèle métier principal

```mermaid
classDiagram
    class User {
        +int id
        +string email
        +string full_name
        +string hashed_password
        +bool is_active
    }

    class Role {
        +int id
        +string name
        +string description
    }

    class UserRole {
        +int id
        +int user_id
        +int role_id
    }

    class Shop {
        +int id
        +int owner_id
        +string name
        +string slug
        +string currency
        +bool is_active
    }

    class ShopAdmin {
        +int id
        +int shop_id
        +int user_id
        +bool can_manage_catalog
        +bool can_manage_orders
        +bool can_manage_admins
    }

    class Address {
        +int id
        +int user_id
        +string label
        +string city
        +string country
        +bool is_default
    }

    class Category {
        +int id
        +int shop_id
        +string name
    }

    class Product {
        +int id
        +int shop_id
        +int category_id
        +string name
        +string sku
        +decimal price
        +int stock_quantity
        +bool is_active
    }

    class Cart {
        +int id
        +int user_id
        +int shop_id
        +string status
        +decimal total_amount
    }

    class CartItem {
        +int id
        +int cart_id
        +int product_id
        +int quantity
        +decimal unit_price
    }

    class Order {
        +int id
        +int user_id
        +int shop_id
        +int address_id
        +string status
        +decimal total_amount
    }

    class OrderItem {
        +int id
        +int order_id
        +int product_id
        +string product_name
        +string sku
        +decimal unit_price
        +int quantity
    }

    class OrderStatusHistory {
        +int id
        +int order_id
        +string status
        +datetime changed_at
    }

    class Payment {
        +int id
        +int order_id
        +string provider
        +string status
        +decimal amount
        +string transaction_reference
    }

    class Shipment {
        +int id
        +int order_id
        +string carrier
        +string tracking_number
        +string status
    }

    User "1" --> "0..*" Shop : possède
    User "1" --> "0..*" Address : possède
    User "1" --> "0..*" Cart : utilise
    User "1" --> "0..*" Order : passe
    User "1" --> "0..*" UserRole : reçoit
    Role "1" --> "0..*" UserRole : attribué via

    Shop "1" --> "0..*" ShopAdmin : délègue à
    User "1" --> "0..*" ShopAdmin : administre

    Shop "1" --> "0..*" Category : contient
    Shop "1" --> "0..*" Product : vend
    Shop "1" --> "0..*" Cart : isole
    Shop "1" --> "0..*" Order : reçoit

    Category "1" --> "0..*" Product : classe
    Cart "1" --> "0..*" CartItem : contient
    Product "1" --> "0..*" CartItem : référencé par

    Order "1" --> "1..*" OrderItem : contient
    Product "1" --> "0..*" OrderItem : référencé par
    Order "1" --> "1..*" OrderStatusHistory : historise
    Order "1" --> "0..*" Payment : paiements
    Order "1" --> "0..1" Shipment : expédition
    Address "1" --> "0..*" Order : utilisée pour
```

### Diagramme de cas d’utilisation

```mermaid
flowchart LR
    Client[Client]
    Proprietaire[Propriétaire de boutique]
    AdminBoutique[Administrateur de boutique]
    AdminPlateforme[Administrateur plateforme]

    UC1((S'inscrire et se connecter))
    UC2((Gérer son profil et ses adresses))
    UC3((Consulter le catalogue))
    UC4((Gérer son panier))
    UC5((Passer une commande))
    UC6((Payer une commande))
    UC7((Suivre une commande))
    UC8((Retourner une commande))

    UC9((Créer et gérer ses boutiques))
    UC10((Déléguer l'administration d'une boutique))
    UC11((Gérer les catégories))
    UC12((Gérer les produits et le stock))
    UC13((Consulter les commandes de la boutique))
    UC14((Confirmer une commande))
    UC15((Valider un paiement))
    UC16((Expédier une commande))
    UC17((Confirmer une livraison))

    UC18((Gérer les rôles globaux))

    Client --> UC1
    Client --> UC2
    Client --> UC3
    Client --> UC4
    Client --> UC5
    Client --> UC6
    Client --> UC7
    Client --> UC8

    Proprietaire --> UC1
    Proprietaire --> UC9
    Proprietaire --> UC10
    Proprietaire --> UC11
    Proprietaire --> UC12
    Proprietaire --> UC13
    Proprietaire --> UC14
    Proprietaire --> UC15
    Proprietaire --> UC16
    Proprietaire --> UC17

    AdminBoutique --> UC1
    AdminBoutique --> UC11
    AdminBoutique --> UC12
    AdminBoutique --> UC13
    AdminBoutique --> UC14
    AdminBoutique --> UC15
    AdminBoutique --> UC16
    AdminBoutique --> UC17

    AdminPlateforme --> UC1
    AdminPlateforme --> UC18
```

## Principaux domaines métier

**Identité** — inscription, connexion, JWT access/refresh, changement de mot de passe et rôles globaux.

**Multi-boutiques** — un utilisateur peut posséder plusieurs boutiques ; des administrateurs peuvent recevoir des permissions granulaires sur une boutique donnée.

**Catalogue** — catégories et produits isolés par boutique, SKU unique au sein d’une boutique, gestion du stock et des règles de disponibilité.

**Panier** — un seul panier actif par utilisateur et par boutique, ajout/mise à jour des articles, validation des quantités et recalcul automatique des totaux.

**Commandes** — création depuis le panier, consultation, liste, mise à jour avant confirmation, annulation, confirmation, expédition, livraison, retour et historique d’état.

**Paiements** — initiation, succès/échec et remboursement lors d’une annulation ou d’un retour. L’intégration à un prestataire de paiement reste isolée derrière le service de paiement.

**Livraison et notifications** — domaines séparés afin que la logique de commande ne dépende pas directement d’un transporteur ou d’un fournisseur de messagerie spécifique.

## Structure du dépôt

```text
shopflow/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   ├── router.py
│   │   └── routes/
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── alembic/
│   └── versions/
├── docs/
│   ├── START_HERE.md
│   ├── ARCHITECTURE.md
│   ├── API_CONTRACTS.md
│   └── TESTING.md
├── scripts/
│   └── seed_roles.py
├── tests/
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Stack technique

- Python 3.11+
- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Alembic
- Pydantic v2
- Authentification JWT
- Hachage des mots de passe avec Argon2
- Pytest

## Démarrage rapide

### 1. Démarrer PostgreSQL

```bash
docker compose up -d postgres
```

### 2. Installer les dépendances

```bash
poetry install
```

### 3. Configurer l’environnement

Linux/macOS :

```bash
cp .env.example .env
```

Windows PowerShell :

```powershell
Copy-Item .env.example .env
```

Pense à remplacer `SECRET_KEY` avant toute utilisation en dehors d’un environnement local de développement.

### 4. Créer le schéma de base de données

```bash
poetry run alembic upgrade head
```

### 5. Lancer l’API

```bash
poetry run uvicorn app.main:app --reload
```

Accès utiles :

- Swagger UI : `http://127.0.0.1:8000/docs`
- ReDoc : `http://127.0.0.1:8000/redoc`
- OpenAPI JSON : `http://127.0.0.1:8000/openapi.json`
- Santé de l’application : `http://127.0.0.1:8000/health`

## Contrôles qualité

ShopFlow n’est pas considéré comme prêt à intégrer simplement parce que quelques scénarios heureux passent. La CI valide le backend à plusieurs niveaux :

- compilation Python et contrôles statiques Ruff ;
- tests des contrats requête/réponse et du schéma OpenAPI ;
- authentification, refresh token et échecs d’autorisation ;
- isolation multi-boutiques et permissions déléguées ;
- règles catalogue, adresse, panier et contraintes d’unicité en base ;
- transitions d’état des commandes, annulation, paiement et retour ;
- migration PostgreSQL 16 depuis une base vide ;
- `alembic check` pour détecter les écarts entre modèles et migrations ;
- downgrade complet d’Alembic jusqu’à `base`, puis remontée jusqu’à `head` ;
- exécution de la suite d’intégration sur PostgreSQL, et pas uniquement SQLite ;
- scénario E2E HTTP réel contre un processus Uvicorn en cours d’exécution et PostgreSQL.

La suite locale rapide se lance avec :

```bash
poetry run pytest -q
```

La validation PostgreSQL et le scénario E2E réel sont reproduits automatiquement par GitHub Actions. Voir [`docs/TESTING.md`](docs/TESTING.md) pour la matrice de tests détaillée.

## Surface de l’API

L’API est versionnée sous `/api/v1`.

```text
/auth/*                         identité + JWT
/users/*                        profil de l’utilisateur courant
/addresses/*                    adresses client
/shops/*                        propriété et administration multi-boutiques
/shops/{shop_id}/categories/*   catalogue de la boutique
/shops/{shop_id}/products/*     produits de la boutique
/shops/{shop_id}/cart/*         panier client par boutique
/shops/{shop_id}/orders         file de commandes de la boutique
/orders/*                       cycle de vie des commandes
/orders/{id}/payments/*         cycle de vie des paiements
/admin/*                        rôles globaux de la plateforme
```

Pour apprendre à lire le projet dans le bon ordre, voir **[docs/START_HERE.md](docs/START_HERE.md)**.

Pour la liste complète des requêtes et réponses, voir **[docs/API_CONTRACTS.md](docs/API_CONTRACTS.md)**.

Pour les choix d’architecture, les responsabilités de la couche de services et les frontières de la base de données, voir **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## Principes de conception

- **Les routers gèrent HTTP ; les services portent la logique métier.**
- **Toute modification liée à une boutique vérifie les permissions de cette boutique.**
- **Les statuts d’une commande ne sont pas modifiés directement par un simple patch.**
- **Les workflows impliquant plusieurs domaines sont coordonnés dans `order_service`.**
- **Les prestataires de paiement, livraison et notification restent remplaçables.**
- **L’historique d’une commande reste cohérent même si le catalogue change ensuite.**

---

ShopFlow est volontairement structuré comme un vrai backend sans transformer chaque fonction en dossier séparé. Le code doit rester assez lisible pour servir de support d’apprentissage, tout en exposant les décisions d’architecture attendues dans un projet Python orienté production.
