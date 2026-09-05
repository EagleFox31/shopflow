# ShopFlow

ShopFlow is a training e-commerce backend used to build practical Python backend skills while progressing toward PCAP-level confidence.

## Restored checkpoint

This repository has been rebuilt to match the last confirmed learning checkpoint before authentication:

- FastAPI API
- PostgreSQL + SQLAlchemy
- Alembic migrations
- Category and Product models
- Product create/read/update/delete
- pagination and basic HTTP error handling
- Pytest API tests

Authentication, JWT and roles are intentionally **not implemented yet**. They are the next milestone.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the complete tree, responsibilities and next steps.

## Run locally

```bash
poetry install
cp .env.example .env
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

On Windows PowerShell, copy the environment file with:

```powershell
Copy-Item .env.example .env
```

The API documentation is available at `http://127.0.0.1:8000/docs`.

## Tests

```bash
poetry run pytest
```

## Current endpoints

- `GET /health`
- `GET /categories/`
- `POST /categories/`
- `GET /products/`
- `GET /products/{product_id}`
- `POST /products/`
- `PUT /products/{product_id}`
- `DELETE /products/{product_id}`

## Learning rule

The codebase stays deliberately simple at this checkpoint. More abstraction will be added only when the domain needs it, so each architectural step remains understandable and explainable by the learner.
