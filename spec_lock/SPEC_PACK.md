SPEC PACK — reservation-service
1. Mission
1.1 System Purpose

reservation-service is a reliability-focused backend service that manages inventory reservations with strict transactional and concurrency correctness. When complete, it exposes a small HTTP API that allows clients to create reservations against inventory, confirm or cancel them, and inspect inventory levels. The primary user is an internal system or service that needs deterministic, race-safe inventory allocation. The invariant that must always hold true is:

reserved_quantity must never exceed total_quantity for any SKU.

No oversell is permitted under any concurrency scenario.

2. Scope Definition
2.1 In Scope

Create reservation (idempotent)

Retrieve reservation by ID

Confirm reservation (idempotent)

Cancel reservation (idempotent)

Retrieve inventory by SKU

Atomic conditional inventory updates

Deterministic conflict semantics (409)

Explicit transaction boundaries

Concurrency correctness validation

Structured error envelope

Health endpoints (liveness + readiness)

2.2 Out of Scope

Authentication / RBAC

Payments

Multi-warehouse inventory

Background expiration workers

Event streaming

Caching layer

Distributed locking

Horizontal scaling claims

UI

Rate limiting

AI integrations

2.3 Non-Goals

Optimizing read throughput

Supporting partial reservations

Supporting inventory adjustments API

Supporting batch reservations

Supporting distributed coordination

Supporting soft-deletes

This service demonstrates correctness, not feature breadth.

3. Domain Model
3.1 Entities
Entity	Purpose	Owner	Persistence	Notes
InventoryItem	Represents stock for a SKU	Domain	Postgres	Unique by SKU
Reservation	Represents a claim against inventory	Domain	Postgres	Idempotent by idempotency_key
InventoryItem

id (UUID)

sku (string, unique)

total_quantity (int ≥ 0)

reserved_quantity (int ≥ 0)

created_at

updated_at

Reservation

id (UUID)

sku (string, FK-like relationship but no strict FK required)

quantity (int > 0)

status (enum)

idempotency_key (string, unique)

created_at

updated_at

3.2 Invariants

reserved_quantity <= total_quantity

Reservation create is idempotent by idempotency_key

Confirm/cancel operations are idempotent

Reservation status transitions must be legal

Inventory + reservation mutations must be atomic

Reservation quantity must be > 0

SKU must exist before reservation

Enforced via:

DB constraints (unique, non-negative, conditional update)

Domain logic

Transaction boundaries

4. State Model

Embedded in this document (declared in FREEZE.md at freeze).

4.1 States

active

confirmed (terminal)

canceled (terminal)

4.2 Legal Transitions
From	To	Condition	Enforced Where
active	confirmed	Always allowed	Domain layer
active	canceled	Always allowed	Domain layer
4.3 Illegal Transitions

confirmed → anything → 409 illegal_state_transition

canceled → anything → 409 illegal_state_transition

confirm confirmed → idempotent success (no-op)

cancel canceled → idempotent success (no-op)

Illegal transitions are tested.

5. Interface / API Contract
5.1 Endpoints
Method	Path	Purpose	Idempotent?
POST	/reservations	Create reservation	Yes
GET	/reservations/{id}	Retrieve reservation	N/A
POST	/reservations/{id}/confirm	Confirm reservation	Yes
POST	/reservations/{id}/cancel	Cancel reservation	Yes
GET	/inventory/{sku}	Retrieve inventory	N/A
5.2 Request Models
POST /reservations

Fields:

sku (string, required)

quantity (int > 0, required)

idempotency_key (string, required)

Validation:

quantity > 0

sku non-empty

idempotency_key non-empty

5.3 Response Models

Reservation Response:

id

sku

quantity

status

created_at

updated_at

Inventory Response:

sku

total_quantity

reserved_quantity

5.4 Error Envelope Contract

All errors:

{
  "error": {
    "code": "machine_identifier",
    "message": "human readable explanation"
  }
}

Error Codes:

invalid_input

sku_not_found

insufficient_inventory

duplicate_idempotency_key

illegal_state_transition

reservation_not_found

database_unavailable

timeout

internal_error

Duplicate idempotency policy:

If idempotency_key already exists:
→ Return existing reservation (200) deterministically.
Not 409.

This ensures safe client retry semantics.

6. Failure Matrix
Scenario	Detected At	User Response	HTTP	Log	Retry?	Idempotent?
Invalid input	Validation	invalid_input	422	INFO	No	N/A
SKU not found	Service	sku_not_found	404	INFO	No	Yes
Duplicate idempotency	DB constraint	return existing	200	INFO	Yes	Yes
Insufficient inventory	Conditional update rowcount=0	insufficient_inventory	409	INFO	Yes	Yes
Illegal transition	Domain	illegal_state_transition	409	WARNING	No	Yes
Reservation not found	Service	reservation_not_found	404	INFO	No	Yes
DB unavailable	Infrastructure	database_unavailable	503	ERROR	Yes	Safe
Timeout	Infra/API	timeout	504	ERROR	Yes	Safe
Partial transaction	Transaction rollback	deterministic rollback	500	ERROR	Safe	Safe

No unmodeled failures allowed.

7. Transaction Model

All mutations use:

with session.begin():

Atomic operations:

Reservation creation:

Verify SKU exists

Conditional inventory update:
UPDATE inventory
SET reserved_quantity = reserved_quantity + qty
WHERE sku = :sku
AND reserved_quantity + :qty <= total_quantity

If rowcount == 0 → insufficient_inventory

Insert Reservation row

All inside one transaction.

Confirm:

Only updates status (no inventory mutation)

Cancel:

Decrement inventory reserved_quantity atomically

Update reservation status

Must be inside same transaction

Idempotency achieved by:

Unique constraint on idempotency_key

IntegrityError mapped deterministically

Isolation expectation:

Default Postgres READ COMMITTED sufficient due to atomic conditional update.

8. Concurrency Model

Optimistic locking:

Not used.

Version column not required.

Concurrency control:

Atomic conditional UPDATE for reservation

Row-level locking implicit in UPDATE

Duplicate request handling:

Unique constraint handles idempotency

Confirm/cancel re-entry safe (idempotent no-op)

Two concurrent reservations exceeding inventory:

Only one succeeds

Others receive 409 insufficient_inventory

Two concurrent confirm calls:

First updates

Second returns stable result

No distributed locking.

9. Observability
9.1 Logging

Structured JSON logging

INFO for conflicts

WARNING for illegal transitions

ERROR for DB failure

No secrets

Errors logged once at API boundary

9.2 Health

Liveness:

Returns 200 if process alive

Readiness:

DB reachable

Migration level compatible

9.3 Metrics

None required.
Logging sufficient.

10. Constraints

Adopts Backend Stack Profile v1.0:

Python 3.12

FastAPI

Pydantic v2

SQLAlchemy 2.x

PostgreSQL

Alembic

pytest

ruff

black

mypy

GitHub Actions CI

Docker + docker-compose

No additional dependencies planned.

11. Complexity Budget

Max endpoints: 5

Max entities: 2

Max background processes: 0

LOC target: 2.5k–3.5k

Max abstraction layers: 3

12. Testing Strategy

Unit Tests:

State transitions

Domain invariants

Idempotency logic

Integration Tests:

Reservation create

Confirm/cancel

Inventory retrieval

Error mapping

Concurrency Test:

total_quantity = 10

20 concurrent requests

Assert reserved_quantity == 10

Losers receive 409

Migration Test:

Upgrade + downgrade validation

Coverage target: 80–85%

Illegal transitions tested explicitly.

13. Security Considerations

No authentication (explicitly out of scope)

Input validation via Pydantic

No PII stored

Secrets via environment variables

No logging of sensitive data

14. Operational Considerations

Environment Variables:

DATABASE_URL

Startup:

App start

Readiness check

Migrations applied via make migrate

Rollback:

Alembic downgrade supported

Deployment:

Single Postgres node assumed

No horizontal scaling

15. Tradeoffs

Why no optimistic locking?

Conditional update sufficient

Simpler model

Clearer demonstration of atomic DB constraint usage

Why no distributed lock?

Not required

Would obscure core invariant

At 10x scale:

Bottleneck: DB write contention

Mitigation: connection pool tuning

First extraction: inventory reservation into dedicated service

First thing likely to break:

Write throughput on single DB node.

16. Definition of Done

 Spec Pack complete

 Scope frozen

 FREEZE.md committed

 Constraints frozen

 Failure matrix complete

 State model complete

 Concurrency model defined

 Complexity budget declared

 Tests passing

 CI passing

 No TODO placeholders

 Documentation complete

 Interview Defense doc written

17. Risk Register

Technical Risk:

Incorrect conditional update logic → Mitigation: concurrency test

Operational Risk:

DB misconfiguration → Mitigation: readiness check

Complexity Risk:

Over-abstracting service layer → Mitigation: strict layer enforcement

Owner: Engineer
Monitoring cadence: Per PR
Trigger condition: Failing concurrency test