# Commencer ici — Parcours d’apprentissage ShopFlow

Ce document est destiné à une personne qui connaît déjà les bases de Python et qui veut comprendre comment une API backend réelle est structurée.

ShopFlow n’est pas un tutoriel « Hello World ». Le projet combine FastAPI, SQLAlchemy, PostgreSQL, Alembic, Pydantic, JWT, permissions multi-boutiques et tests. L’objectif de ce parcours est donc de **lire le projet dans le bon ordre**, sans commencer directement par les fichiers les plus complexes.

---

## Prérequis conseillés

Avant de commencer, il est préférable de savoir utiliser :

- variables, conditions, boucles et fonctions Python ;
- classes et objets ;
- listes et dictionnaires ;
- imports et modules ;
- exceptions avec `try` / `except` ;
- environnements virtuels ;
- bases de HTTP : `GET`, `POST`, `PUT`, `DELETE`, codes `200`, `201`, `400`, `401`, `403`, `404`, `409`, `422` ;
- notions SQL simples : table, colonne, clé primaire, clé étrangère.

Si ces notions sont encore fragiles, ShopFlow peut servir de projet à observer, mais il vaut mieux consolider les bases avant de modifier le code.

---

# Le fil conducteur

Pour comprendre une fonctionnalité ShopFlow, suis toujours ce chemin :

```text
Base de données
      ↓
Model SQLAlchemy
      ↓
Schema Pydantic
      ↓
Service métier
      ↓
Router FastAPI
      ↓
Contrat HTTP / OpenAPI
      ↓
Tests
```

Une bonne première fonctionnalité à suivre est **Produit** : elle est assez simple pour comprendre l’architecture sans commencer immédiatement par le workflow des commandes.

---

# Étape 0 — Faire tourner le projet

Avant de lire beaucoup de code, vérifie que l’application démarre.

```bash
docker compose up -d postgres
poetry install
cp .env.example .env
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

Sous Windows PowerShell :

```powershell
Copy-Item .env.example .env
```

Puis ouvre :

- Swagger : `http://127.0.0.1:8000/docs`
- ReDoc : `http://127.0.0.1:8000/redoc`
- OpenAPI : `http://127.0.0.1:8000/openapi.json`
- Santé : `http://127.0.0.1:8000/health`

### À comprendre

- `app/main.py` crée l’application FastAPI ;
- `app/api/router.py` rassemble les routes ;
- `app/core/config.py` charge la configuration ;
- `app/db/session.py` configure la connexion à la base.

### Mini-exercice

Trouve dans `app/main.py` où le router principal est enregistré dans l’application.

**Checkpoint :** tu dois pouvoir expliquer comment une requête HTTP arrive jusqu’à une route ShopFlow.

---

# Étape 1 — Comprendre le modèle de données

Commence par le diagramme de classes du `README.md`, puis ouvre quelques modèles simples :

```text
app/models/user.py
app/models/shop.py
app/models/category.py
app/models/product.py
```

Ensuite seulement :

```text
app/models/cart.py
app/models/cart_item.py
app/models/order.py
app/models/order_item.py
app/models/order_status_history.py
app/models/payment.py
app/models/shipment.py
```

### Questions à te poser

- Pourquoi `Shop` possède-t-il un `owner_id` ?
- Pourquoi `Product` est-il lié à une boutique ?
- Pourquoi un panier appartient-il à la fois à un utilisateur et à une boutique ?
- Pourquoi `OrderItem` conserve-t-il les données du produit au moment de la commande ?
- À quoi sert `OrderStatusHistory` ?

### Mini-exercice

Dessine à la main les relations :

```text
User → Shop → Product
User → Cart → CartItem → Product
User → Order → OrderItem
```

Puis compare ton dessin au diagramme du README.

**Checkpoint :** tu dois pouvoir expliquer pourquoi ShopFlow est multi-boutiques et pourquoi les données métier doivent être isolées par boutique.

---

# Étape 2 — Comprendre SQLAlchemy et les migrations

Lis ensuite :

```text
app/db/base.py
app/db/session.py
alembic/env.py
alembic/versions/20260905_0001_full_shopflow_schema.py
alembic/versions/20260905_0002_active_cart_constraint.py
```

### À comprendre

- différence entre un modèle Python et une table PostgreSQL ;
- `primary_key`, `foreign_key`, `relationship` ;
- contraintes d’unicité ;
- rôle d’Alembic ;
- différence entre `alembic upgrade head` et `alembic downgrade base`.

### Mini-exercice

Repère la contrainte qui empêche plusieurs paniers actifs pour le même couple utilisateur/boutique.

**Checkpoint :** tu dois être capable d’expliquer pourquoi modifier un modèle SQLAlchemy ne suffit pas toujours : la base doit aussi recevoir une migration.

---

# Étape 3 — Comprendre les contrats avec Pydantic

Explore le dossier :

```text
app/schemas/
```

Commence par les schemas de produit et de boutique avant les commandes.

Cherche les variantes du type :

```text
Create
Read
Update
```

### À comprendre

Un `Model` SQLAlchemy décrit principalement **comment les données vivent en base**.

Un `Schema` Pydantic décrit principalement **ce que l’API accepte ou renvoie**.

Ces deux responsabilités ne sont pas les mêmes.

### Mini-exercice

Compare le modèle `Product` à ses schemas Pydantic et note les champs :

1. fournis par le client ;
2. générés par l’application ;
3. renvoyés dans la réponse.

**Checkpoint :** tu dois pouvoir expliquer pourquoi on n’envoie pas directement un objet SQLAlchemy brut comme contrat public de l’API.

---

# Étape 4 — Suivre une fonctionnalité simple de bout en bout

Prends **Produit** comme premier cas complet.

Lis dans cet ordre :

```text
app/models/product.py
      ↓
app/schemas/product.py
      ↓
app/services/product_service.py
      ↓
app/api/routes/products.py
      ↓
tests/test_addresses_cart_catalog.py
```

### À observer

Dans le router :

- récupération des paramètres HTTP ;
- dépendances ;
- utilisateur courant ;
- appel au service ;
- code de réponse.

Dans le service :

- règles métier ;
- autorisations ;
- requêtes SQLAlchemy ;
- validations propres au domaine.

### Mini-exercice

Réponds à cette question sans exécuter le code :

> Que se passe-t-il depuis `POST /shops/{shop_id}/products` jusqu’au `INSERT` en base ?

Puis vérifie ta réponse en suivant les appels dans le code.

**Checkpoint :** tu dois être capable de tracer une requête `HTTP → Router → Service → DB → Response`.

---

# Étape 5 — Comprendre la Service Layer

Lis :

```text
app/services/category_service.py
app/services/product_service.py
app/services/cart_service.py
app/services/cart_item_service.py
app/services/address_service.py
```

Puis lis `docs/ARCHITECTURE.md`.

ShopFlow a volontairement déplacé la logique métier hors des routers.

```text
Mauvais objectif :
Router = HTTP + SQL + règles métier + permissions + transactions

Objectif ShopFlow :
Router = HTTP + validation + appel service
Service = règles métier + accès DB + orchestration
```

### Mini-exercice

Prends une route de `products.py` et identifie ce qui aurait rendu le router trop lourd si toute la logique du service y était recopiée.

**Checkpoint :** tu dois pouvoir expliquer la différence entre une route et un service métier.

---

# Étape 6 — Comprendre le multi-boutiques et les permissions

Lis :

```text
app/models/shop.py
app/models/shop_admin.py
app/services/shop_service.py
app/services/shop_admin_service.py
app/api/routes/shops.py
app/api/deps.py
tests/test_multishop.py
```

Puis regarde :

```text
app/models/role.py
app/models/user_role.py
app/services/role_service.py
app/services/user_role_service.py
```

### Idée importante

Les rôles globaux de la plateforme ne sont pas la même chose que les permissions sur une boutique.

Exemple :

```text
Utilisateur A
├── propriétaire de Boutique 1
├── propriétaire de Boutique 2
└── administrateur délégué de Boutique 3
```

Le backend ne doit jamais supposer que connaître `shop_id` suffit à avoir accès à la boutique.

### Mini-exercice

Dans `tests/test_multishop.py`, repère un scénario où un utilisateur tente d’accéder à une boutique qui ne lui appartient pas.

**Checkpoint :** tu dois pouvoir expliquer la différence entre authentification et autorisation.

---

# Étape 7 — Comprendre l’authentification JWT

Lis dans cet ordre :

```text
app/core/security.py
app/services/token_service.py
app/services/auth_service.py
app/services/user_service.py
app/api/deps.py
app/api/routes/auth.py
tests/test_auth.py
```

### À comprendre

- hash du mot de passe ;
- vérification du mot de passe ;
- access token ;
- refresh token ;
- récupération de l’utilisateur courant ;
- différence entre `401 Unauthorized` et `403 Forbidden`.

### Mini-exercice

Explique ce qui se passe si :

1. le JWT est absent ;
2. le JWT est invalide ;
3. le JWT est valide mais l’utilisateur n’a pas le droit d’administrer la boutique.

**Checkpoint :** tu dois savoir dire où s’arrête l’authentification et où commence l’autorisation métier.

---

# Étape 8 — Comprendre le panier

Lis :

```text
app/models/cart.py
app/models/cart_item.py
app/services/cart_service.py
app/services/cart_item_service.py
app/api/routes/cart.py
tests/test_addresses_cart_catalog.py
```

### À observer

- panier actif par utilisateur et boutique ;
- validation du produit ;
- validation de la quantité ;
- calcul du total ;
- lien avec le stock.

### Mini-exercice

Imagine qu’un utilisateur ajoute deux fois le même produit. Cherche dans le code si ShopFlow crée deux lignes ou met à jour la quantité existante.

**Checkpoint :** tu dois pouvoir expliquer comment le panier prépare les données utilisées ensuite par la commande.

---

# Étape 9 — Comprendre `OrderService`, seulement maintenant

`app/services/order_service.py` est l’un des fichiers les plus importants du projet. Ne commence pas le repo par lui.

Lis avant lui :

```text
app/models/enums.py
app/models/order.py
app/models/order_item.py
app/models/order_status_history.py
app/models/payment.py
app/models/shipment.py
```

Puis :

```text
app/services/order_service.py
app/services/payment_service.py
app/services/shipment_service.py
app/api/routes/orders.py
app/api/routes/payments.py
```

Et enfin les tests :

```text
tests/test_order_lifecycle.py
tests/test_order_rules.py
tests/test_payments_and_returns.py
```

### Cycle principal

```text
PENDING
   ↓ paiement réussi
PAID
   ↓ confirmation boutique
CONFIRMED
   ↓ expédition
SHIPPED
   ↓ livraison
DELIVERED
   ↓ retour éventuel
RETURNED
```

Certaines étapes autorisent également une annulation.

### Questions à te poser

- Qui a le droit de faire chaque transition ?
- Pourquoi une commande ne peut-elle pas passer directement de `PENDING` à `DELIVERED` ?
- À quel moment le stock est-il réservé ?
- Quand est-il restauré ?
- Pourquoi les changements de statut sont-ils historisés ?

### Mini-exercice

Choisis `cancel_order()` ou `return_order()` et dessine tous les services qu’il doit contacter.

**Checkpoint :** tu dois pouvoir expliquer pourquoi `OrderService` est un orchestrateur métier et pas un simple CRUD.

---

# Étape 10 — Comprendre les tests

Commence petit :

```text
tests/test_health.py
```

Puis :

```text
tests/test_auth.py
tests/test_multishop.py
tests/test_addresses_cart_catalog.py
tests/test_order_lifecycle.py
```

Ensuite :

```text
tests/test_order_rules.py
tests/test_payments_and_returns.py
tests/test_database_constraints.py
tests/test_openapi_contract.py
```

Et termine avec :

```text
tests/e2e/
.github/workflows/ci.yml
```

Lis aussi [`TESTING.md`](TESTING.md).

### À comprendre

Il existe plusieurs niveaux de validation :

```text
Tests métier / intégration rapides
        ↓
Contrats OpenAPI
        ↓
Contraintes PostgreSQL réelles
        ↓
Migrations Alembic
        ↓
Serveur Uvicorn réel
        ↓
E2E HTTP
```

### Mini-exercice

Prends une règle métier du projet et trouve :

1. le code qui l’implémente ;
2. le test qui prouve qu’elle fonctionne ;
3. le test qui prouve qu’un cas invalide est refusé.

**Checkpoint :** tu dois comprendre qu’un test « happy path » seul ne suffit pas à valider un backend.

---

# Étape 11 — Lire les contrats API

Une fois l’architecture comprise, lis [`API_CONTRACTS.md`](API_CONTRACTS.md) et compare-le à Swagger.

Observe pour chaque endpoint :

- méthode HTTP ;
- URL ;
- authentification requise ;
- body de requête ;
- schema de réponse ;
- codes d’erreur possibles.

### Mini-exercice

Choisis une fonctionnalité et vérifie que les trois représentations sont cohérentes :

```text
Schema Pydantic
      ↕
Route FastAPI
      ↕
OpenAPI / Swagger
```

---

# Parcours conseillé en trois passes

## Passe 1 — Comprendre sans modifier

Lis uniquement :

```text
README.md
app/main.py
app/models/
app/schemas/
app/services/product_service.py
app/api/routes/products.py
```

Objectif : comprendre la forme générale du projet.

## Passe 2 — Suivre les domaines

Étudie successivement :

```text
Catalogue
→ Panier
→ Authentification
→ Multi-boutiques
→ Commandes
→ Paiements
→ Livraison
```

Objectif : comprendre les responsabilités de chaque service.

## Passe 3 — Modifier et tester

Choisis une petite amélioration, écris d’abord le comportement attendu, ajoute ou modifie le test, puis touche au code.

Objectif : apprendre à travailler sans casser les règles existantes.

---

# Premières contributions adaptées à un débutant backend

Voici de bons exercices, du plus simple au plus difficile :

1. ajouter un filtre de recherche produit par nom ;
2. ajouter un tri produit par prix ;
3. ajouter une pagination à une liste qui n’en possède pas ;
4. ajouter un champ facultatif à une adresse avec migration + schema + tests ;
5. ajouter une règle de validation sur le stock ;
6. ajouter un nouvel événement dans l’historique d’une commande ;
7. ajouter une permission ShopAdmin et les tests correspondants ;
8. ajouter un endpoint métier avec contrat OpenAPI complet.

Pour chaque exercice, respecte toujours la même chaîne :

```text
Besoin
→ règle métier
→ modèle/migration si nécessaire
→ schema
→ service
→ route
→ tests
→ documentation
```

---

# Ce qu’il faut éviter au début

Évite comme première modification :

- réécrire `order_service.py` ;
- modifier toutes les relations SQLAlchemy en même temps ;
- changer le système JWT sans tests ;
- supprimer une migration existante ;
- déplacer la logique métier dans les routers ;
- contourner les contrôles d’accès avec un simple `shop_id` ;
- considérer qu’un endpoint fonctionne uniquement parce qu’il renvoie `200`.

---

# Quand considérer que tu as compris ShopFlow ?

Tu n’as pas besoin de mémoriser chaque fichier. En revanche, tu devrais pouvoir répondre clairement à ces questions :

- Comment une requête HTTP traverse-t-elle ShopFlow ?
- Quelle est la différence entre Model, Schema, Service et Router ?
- Pourquoi un utilisateur peut-il avoir plusieurs boutiques ?
- Comment ShopFlow empêche-t-il l’accès à la boutique d’un autre utilisateur ?
- Comment fonctionne un access token ?
- Comment un panier devient-il une commande ?
- Pourquoi les transitions de statut sont-elles contrôlées ?
- Quand le stock diminue-t-il et quand est-il restauré ?
- À quoi sert Alembic ?
- Quelle différence existe entre un test d’intégration et un E2E réel ?

Si tu peux expliquer ces points sans lire le code ligne par ligne, tu as déjà compris l’essentiel de l’architecture.

---

## Documents à lire ensuite

- [`README.md`](../README.md) — vision générale, architecture et diagrammes UML ;
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — décisions d’architecture et responsabilités ;
- [`API_CONTRACTS.md`](API_CONTRACTS.md) — contrats HTTP ;
- [`TESTING.md`](TESTING.md) — stratégie et matrice de tests.

ShopFlow doit servir à apprendre à **raisonner sur un backend**, pas seulement à recopier du code.