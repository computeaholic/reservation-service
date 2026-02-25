Stack Alignment Check — reservation-service
1️⃣ Language

Python 3.12
Pinned in pyproject.toml.

No async worker.
No asyncio dependency needed.

Aligned.

2️⃣ Framework

FastAPI

We are using:

Explicit request models

Explicit response models

Error envelope mapping at API boundary

No magic.
No background tasks.
No dependency injection frameworks.

Aligned.

3️⃣ Validation

Pydantic v2

Used only for:

Request validation

Response shaping

Domain layer remains Pydantic-free.

Aligned.

4️⃣ ORM

SQLAlchemy 2.x (Declarative only)

We must enforce:

No legacy .query

Explicit session.execute

Explicit with session.begin()

No global session

Important:

Reservation creation will use:

update_stmt = (
    update(InventoryItem)
    .where(...)
    .values(...)
)

Not ORM instance mutation followed by flush.

We want explicit SQL expression semantics.

Aligned.

5️⃣ Database

Postgres only.

Important here:

Conditional update enforces invariant.

Unique index on:

sku (inventory)

idempotency_key (reservation)

No SQLite fallback.

Aligned.

6️⃣ Migrations

Alembic required.

We will:

Generate initial schema

Provide downgrade

Test downgrade in CI

No schema drift allowed.

Aligned.

7️⃣ Testing

pytest

Required:

Domain transition tests

Integration tests (API + DB)

Concurrency test (critical)

Migration test (upgrade + downgrade)

Coverage 80–85%

Important:
Concurrency test must be deterministic.
We cannot rely on sleep-based timing flakiness.

Aligned.

8️⃣ Linting & Formatting

ruff
black
mypy

No bypass.
Pre-commit required.

Aligned.

9️⃣ CI

GitHub Actions must enforce:

fmt

lint

typecheck

test

coverage threshold

No bypass.
No soft failures.

Aligned.

🔟 Docker

Must include:

Dockerfile (pinned Python image)

docker-compose.yml

Postgres container

App container

Must provide Make targets:

make up
make down
make fmt
make lint
make typecheck
make test
make migrate
make rollback
make run

We will enforce this.

Aligned.

11️⃣ Error Envelope

We already froze:

{
  "error": {
    "code": "machine_identifier",
    "message": "human readable"
  }
}

All domain exceptions mapped at API boundary.

No raw SQL errors returned.

Aligned.

12️⃣ Transaction Discipline

Every mutation must use:

with session.begin():

No implicit commits.
No autocommit.
No ORM session tricks.

Critical for:

Reservation create

Cancel

Confirm

Aligned.

13️⃣ Idempotency Policy

The profile requires:

IntegrityError mapping to 409

However, we deliberately chose:

Duplicate idempotency_key → return existing reservation (200).

This is still compliant because:

We document duplicate behavior.

We rely on unique constraint.

We map deterministically.

We must explicitly document this divergence in:

FAILURE_MODES.md
and TRADEOFFS.md.

It is not a violation.
It is a documented policy choice.

Aligned.

14️⃣ State Discipline

Reservation state transitions are:

active → confirmed

active → canceled

Illegal transitions tested.
Domain-enforced.

Aligned.

15️⃣ Logging

Structured logging only.
No double logging.
API boundary logs once.

Aligned.

16️⃣ Definition of Done

All requirements already mirrored in our SPEC_PACK.

Aligned.