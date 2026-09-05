# ShopFlow architecture

This document represents the checkpoint reached before starting authentication.

## Current scope

Implemented at this checkpoint:

- FastAPI application entry point
- `/health` endpoint
- PostgreSQL connection through SQLAlchemy
- Alembic migrations
- `Category` model
- `Product` model
- Pydantic schemas for create/read/update
- basic category create/list endpoints
- full Product CRUD
- pagination on product listing
- 404/409/422 error handling for the current domain rules
- API tests with Pytest and an isolated SQLite database

Not implemented yet:

- User model
- password hashing
- register/login
- JWT access tokens
- current-user dependency
- role-based access control
- cart, orders and payments
- Docker/CI/CD hardening

## Project tree

```text
shopflow/
├── app/
│   ├── main.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── category.py
│   │   └── product.py
│   ├── schemas/
│   │   ├── category.py
│   │   └── product.py
│   └── api/
│       └── routes/
│           ├── health.py
│           ├── categories.py
│           └── products.py
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 20260905_0001_create_categories_and_products.py
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   └── test_products.py
├── .env.example
├── alembic.ini
├── pyproject.toml
└── README.md
```

## Request flow

```text
HTTP request
    ↓
FastAPI route
    ↓
Pydantic schema validation
    ↓
SQLAlchemy Session
    ↓
Category / Product model
    ↓
PostgreSQL
```

At this stage, CRUD logic intentionally stays close to the routes so the learning path remains easy to follow. A service/repository layer should only be introduced when domain logic becomes complex enough to justify it.

## Next milestone

Authentication is the next deliberate step:

1. `User` SQLAlchemy model
2. registration schema and endpoint
3. password hashing
4. login endpoint
5. JWT generation/validation
6. `get_current_user`
7. `role` field and admin authorization
8. protect Product create/update/delete for admins

Suggested commit milestone:

```text
feat(auth): JWT login + role-based access
```
