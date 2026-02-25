TRADEOFFS — reservation-service

This document records intentional choices and rejected alternatives.

1. Decision Log
Decision	Alternatives Considered	Why Rejected	Cost of This Choice	Where Enforced
Atomic conditional UPDATE for inventory reservation	Optimistic locking (version column)	Versioning does not prevent oversell without additional constraint logic; conditional UPDATE directly enforces invariant	Less flexibility for complex allocation strategies	Service layer + DB
No optimistic version column on InventoryItem	Version-based lost-update protection	Lost-update is not primary risk; oversell is. Conditional update handles correctness	Cannot easily support concurrent inventory edits without spec change	Domain + schema
Idempotency via unique constraint on idempotency_key	Application-level dedupe table; returning 409 on duplicate	DB constraint is simpler, deterministic, and concurrency-safe	Cannot distinguish between malicious replay and legitimate retry	DB schema + service
Duplicate idempotency returns existing reservation (200)	Return 409 duplicate_idempotency_key	200 ensures safe retry semantics and simpler client logic	Clients cannot distinguish first vs replay without comparing timestamps	API layer
Confirm/cancel idempotent no-op	Strict error on repeated operation	Idempotency simplifies retry and avoids unnecessary 409s	Slightly more domain logic complexity	Domain layer
No distributed locking	Advisory locks; Redis locks	Single DB node; invariant solvable via conditional UPDATE; distributed lock adds complexity without benefit	Does not scale beyond single DB instance	Architecture
No background expiration worker	TTL + async cleanup	Out of scope; adds concurrency surface area	Reservations never auto-expire	Scope definition
No FK constraint between Reservation.sku and InventoryItem.sku	Hard foreign key constraint	Simplifies initial migration and avoids cascading complexity	Data integrity relies on service validation	Service layer
READ COMMITTED isolation (default)	SERIALIZABLE isolation	Conditional update sufficient; SERIALIZABLE adds overhead	Rare phantom scenarios not modeled	DB configuration
Structured error envelope	Raw exception passthrough	Deterministic client contract required	Slight overhead in mapping	API boundary
2. Scope Exclusions
Excluded Feature	Why Not Built	Risk / Cost of Exclusion	When It Would Be Added
Authentication / RBAC	Not core to invariant demonstration	Open API surface	When service exposed externally
Inventory adjustment endpoint	Not required to prove reservation correctness	Manual DB updates required for stock changes	When real inventory management added
Multi-warehouse inventory	Expands domain complexity	Cannot allocate per-location	When domain requires location-aware stock
Background expiration worker	Adds concurrency model complexity	Stale reservations possible	When business requires TTL
Caching layer	Correctness prioritized over read throughput	Higher DB read load	When read scaling required
Distributed locking	Adds operational complexity	Cannot safely scale across DB shards	When horizontally scaled DB introduced
Event streaming	Out of scope	No external integration signals	When integrating with downstream systems
Horizontal scaling claims	Not required for this exercise	Single-node DB bottleneck	When production load demands it
3. Complexity Avoidance

No background processing — avoids additional concurrency surface area.

No distributed locking — invariant solved at database layer.

No optimistic versioning — atomic update sufficient for correctness goal.

No caching layer — avoids invalidation complexity.

No multi-entity aggregates — only 2 entities to preserve clarity.

No generic repository pattern — avoids abstraction theater.

No “domain events” pattern — not required for core invariant.

No soft-delete — avoids hidden state complexity.

No generic error factory — explicit mapping preferred.

4. 10x Scale Notes (Reality-Based)

Bottleneck:

Write contention on InventoryItem rows (hot SKUs).

Mitigation:

Increase connection pool.

Add read replica for GET endpoints.

Partition inventory by SKU hash if needed.

First extraction boundary:

Inventory reservation logic into its own service if:

SKU write contention becomes dominant

Inventory domain expands (multi-location, batching)

System does not scale horizontally without redesign.
Single Postgres node is a conscious assumption.

5. Freeze Rule

Any change to a major decision requires:

Update SPEC_PACK.md

Update this TRADEOFFS.md

Update FREEZE.md with new commit hash

Re-freeze scope if scope changed

Tradeoffs are binding architectural commitments.