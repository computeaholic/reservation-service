INTERVIEW DEFENSE — reservation-service
1. Design Intent

This system implements a minimal inventory reservation service backed by a single PostgreSQL database.
Its primary responsibility is to prevent overselling while supporting idempotent reservation creation and state transitions under concurrent access.
The primary invariant protected is:

reserved_quantity <= total_quantity at all times.

The most important design decision is the use of an atomic conditional UPDATE at the database layer to enforce inventory correctness under contention.

Correctness is enforced through database constraints and explicit transaction boundaries, not application timing assumptions.

2. What This Project Demonstrates

Atomic conditional update to prevent oversell under concurrent requests

Idempotent reservation creation via unique idempotency_key constraint

Idempotent state transitions (confirm/cancel)

Explicit domain-layer enforcement of legal and illegal state transitions

Explicit transaction boundaries using with session.begin():

Deterministic error envelope mapping

Concurrency conflict mapped to stable 409 response

No implicit commits or global session usage

Clear dependency direction: api → services → domain

All behaviors are enforced and tested.

3. Tradeoffs Made
Decision	Alternative Considered	Why Rejected	Cost of This Choice
Atomic conditional update	Optimistic version locking	Versioning does not directly prevent oversell	Harder to extend to complex allocation strategies
Idempotency via DB constraint	Application-level dedupe	DB constraint is deterministic under concurrency	Cannot distinguish replay from first write
No distributed locking	Redis/advisory locks	Single DB node sufficient; extra layer unnecessary	Cannot scale across DB shards without redesign
No background expiration worker	Async cleanup task	Adds concurrency surface and complexity	Reservations never auto-expire
No foreign key from Reservation.sku	Strict relational enforcement	Simplifies migration and avoids cascade complexity	Integrity enforced in service layer
4. Scaling Considerations (10x Scenario)

What fails first:

Write contention on hot SKUs (row-level locking on InventoryItem).

Bottleneck:

Single Postgres node handling all write traffic.

Mitigation:

Increase connection pool limits.

Add read replicas for GET endpoints.

Partition inventory by SKU hash if write contention grows.

First extraction boundary:

Inventory reservation logic into a dedicated service if SKU contention dominates.

What remains stable:

Error contract

Idempotency policy

Transaction model

Domain state enforcement

This system assumes a single-node database.

5. Concurrency & Failure Analysis

Race condition surface:

Multiple concurrent reservation attempts on same SKU.

Prevention:

Single atomic SQL UPDATE with condition:
reserved_quantity + qty <= total_quantity.

Rowcount check determines success or conflict.

Partial failure risk:

Multi-step reservation creation (create row + update inventory).

Prevention:

Wrapped in with session.begin():.

Automatic rollback on exception.

No partial write possible.

Idempotency guarantee:

Unique constraint on idempotency_key.

Duplicate requests return existing reservation deterministically.

Retry safety:

Safe retry: create, confirm, cancel.

Unsafe retry: illegal state transition.

Safe retry after 503 or 504.

6. Operational Readiness

Startup:

Docker Compose brings up Postgres + app container.

App fails readiness if DB unreachable.

Migrations:

Applied via make migrate.

Downgrade supported via make rollback.

Health Checks:

Liveness: process responsive.

Readiness: DB connectivity and migration compatibility verified.

Logging:

Structured logs.

Errors logged once at API boundary.

No stack traces exposed to client.

Failed deployment recovery:

Rollback migration.

Restart container.

No data corruption due to transactional discipline.

7. Known Limits

Single-node PostgreSQL assumption.

No horizontal scaling.

No distributed locking.

No reservation expiration.

No multi-warehouse support.

No rate limiting.

No authentication or authorization.

These limits are intentional and documented in SPEC_PACK and TRADEOFFS.