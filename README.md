# reservation-service

`reservation-service` is a compact Python/PostgreSQL engineering sample focused on transactional reservation correctness under contention. It is intentionally not a booking platform, not an HTTP service, and not a generic architecture template.

## Why this exists

This repository demonstrates a small set of business rules that are easy to state but easy to get wrong under concurrent access: inventory cannot be over-reserved, retries must not double-reserve, conflicting idempotency reuse must be rejected, and terminal state transitions must not overwrite one another.

## Core invariants

- Supported reservation creates cannot oversubscribe inventory.
- Replaying the same `idempotency_key` with the same `sku` and `quantity` returns the original reservation without reserving inventory twice.
- Reusing an `idempotency_key` for a different `sku` or `quantity` is rejected deterministically.
- Cancellation restores inventory exactly once.
- Concurrent confirm and cancel operations cannot both win.
- Mutations are transactionally atomic.

## Transaction model

Reservation creation, confirmation, and cancellation each run inside an explicit `with session.begin():` transaction in `src/services/reservation_service.py`.

Create uses an atomic conditional `UPDATE` on `inventory_items`:

```sql
UPDATE inventory_items
SET reserved_quantity = reserved_quantity + :quantity
WHERE sku = :sku
	AND reserved_quantity + :quantity <= total_quantity
```

If that update affects zero rows, the service distinguishes between a missing SKU and insufficient inventory without partially committing the reservation attempt.

## Idempotency model

`idempotency_key` is backed by a unique database constraint.

- Sequential replay with the same payload returns the existing reservation.
- Conflicting reuse of the same key raises `IdempotencyConflict`.
- Concurrent equivalent requests with the same key converge on one persisted reservation row and one inventory effect.

This repository does not claim "exactly once" delivery semantics. It proves deterministic create semantics inside one PostgreSQL-backed service boundary.

## Concurrency model

- Competing reservation creates rely on the atomic conditional inventory update.
- Confirm and cancel take a row-level lock on the reservation row before deciding the transition.
- Concurrent double-cancel leaves the reservation canceled and restores inventory once.
- Concurrent confirm-vs-cancel yields one winning terminal transition and one deterministic loser.

## Run locally

Prerequisites:

- Python 3.12
- Docker with `docker compose`

Cold-clone setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install .[dev]
make up
make migrate
```

The local test and lint commands use PostgreSQL on `localhost:5432` with the database name `reservation_test`. `make up` provides that database via Docker with local trust authentication, so no password bootstrap step is required.

## Validate

```bash
make lint
make test
make validate-hooks
make rollback
make migrate
```

## What to inspect

- `src/services/reservation_service.py` for transaction boundaries, idempotency handling, and lifecycle concurrency control.
- `tests/test_reservation_service.py` for the business-rule and concurrency proof surface.
- `tests/test_migrations.py` and `alembic/versions/` for migration proof.
- `docs/FAILURE_MATRIX.md` for the compact behavior summary.
- `docs/ARCHITECTURE.md` for a short design note.

## Scope

This sample does not implement:

- an HTTP or RPC API layer
- authentication or authorization
- payments
- queues, workers, or expiration jobs
- distributed locking or cross-service coordination
- caching
- multi-warehouse allocation

## Status

Engineering sample focused on transactional reservation correctness and concurrency-safe business rules.
