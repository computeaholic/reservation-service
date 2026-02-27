# Reservation Service

Postgres-backed reservation domain service with deterministic invariants and transactional behavior.

## What it does

- Creates reservations with idempotency-key replay protection.
- Confirms and cancels reservations with explicit state-transition guards.
- Enforces inventory constraints under concurrency.
- Persists via SQLAlchemy models and Alembic migrations.

## Architecture

- `src/domain/`: pure domain entities, status, and domain exceptions (no SQLAlchemy).
- `src/services/`: orchestration/use-case logic over domain and persistence models.
- `src/infrastructure/`: SQLAlchemy engine/session and persistence models only.
- `tests/`: Postgres-backed deterministic tests for domain, infrastructure, and service invariants.

## Run locally

Prerequisites:

- Python 3.12
- Docker + Docker Compose

Commands:

- `make up` — recreates and starts the compose stack deterministically.
- `make test` — runs Postgres-backed tests with enforced coverage gates.
- `docker compose up` — starts services directly.

## Design decisions

- Uses DB-level constraints plus transactional updates to prevent over-reservation.
- Uses idempotency keys to make create operation replay-safe.
- Uses rollback-scoped test sessions with savepoints for deterministic isolation.
- Keeps strict toolchain gates (`black`, `ruff`, `mypy`, `pytest-cov`) pinned in `pyproject.toml`.
