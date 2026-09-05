# ShopFlow testing strategy

ShopFlow uses layered validation. Passing a small SQLite happy-path suite is not treated as release confidence.

## Fast local suite

The default `pytest` run uses an isolated SQLite database for speed and covers:

- registration, login, JWT access/refresh token types and password changes
- Pydantic request validation and stable error response shape
- generated OpenAPI path/schema coverage
- multi-shop ownership and cross-shop isolation
- delegated `ShopAdmin` permissions
- shop/category/SKU uniqueness conflicts on create and update
- address ownership/default rules and protection of addresses referenced by orders
- product soft deletion and category deletion rules
- cart totals, stock checks, empty/unknown shop errors and one-active-cart DB constraint
- order creation, stock reservation, state transition failures and history
- cancellation with stock release and payment refund
- payment failure/retry, merchant-only manual payment confirmation and wrong-order payment isolation
- shipping, delivery and customer-only return with stock restoration
- platform-role authorization

## PostgreSQL integration gate

GitHub Actions starts a real PostgreSQL 16 service and then runs:

```text
alembic upgrade head
alembic check
alembic downgrade base
alembic upgrade head
pytest -q --ignore=tests/e2e
```

This validates that:

- the schema can be created from an empty PostgreSQL database;
- downgrade and re-upgrade both succeed;
- SQLAlchemy metadata and migrations do not drift;
- PostgreSQL foreign keys, partial indexes and uniqueness constraints behave as expected;
- the same integration tests pass against PostgreSQL, not only SQLite.

## Live HTTP E2E

The CI job then resets the migrated database, launches the real application with Uvicorn, and executes `tests/e2e/test_live_api.py` over HTTP using `httpx`.

The scenario covers:

```text
health + OpenAPI
    ↓
merchant registration/login
customer registration/login
    ↓
shop → category → product
    ↓
customer address → cart → order
    ↓
stock reservation
    ↓
payment initiation
customer self-approval rejected
merchant payment confirmation
    ↓
confirm → ship → deliver
    ↓
customer return
    ↓
stock restored + full status history verified
```

A pull request should not be merged until both CI jobs are green.
