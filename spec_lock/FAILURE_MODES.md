FAILURE_MODES.md — reservation-service

All failure scenarios are explicitly modeled.

No unmodeled failure is acceptable.

All failures are logged exactly once at the API boundary layer during error envelope mapping.

Lower layers (domain/services/infrastructure) do not log.

Failure Matrix
Scenario	Detected At	User Response	HTTP Code	Log Level	Retry Strategy	Idempotent Behavior
Invalid input (schema validation failure)	Validation layer (FastAPI/Pydantic)	{code: invalid_input}	422	INFO	No retry until corrected	N/A
SKU not found during reservation	Service layer	{code: sku_not_found}	404	INFO	No retry unless SKU created	Safe to retry
Reservation not found	Service layer	{code: reservation_not_found}	404	INFO	No retry	Safe to retry
Duplicate idempotency_key (create)	Infrastructure layer (unique constraint)	Return existing reservation	200	INFO	Safe to retry	Protected by DB constraint
Insufficient inventory (conditional update rowcount = 0)	Service layer	{code: insufficient_inventory}	409	INFO	Retry only if inventory changes	Safe to retry
Illegal state transition (confirm/cancel terminal)	Domain layer	{code: illegal_state_transition}	409	WARNING	No retry	Idempotent for same transition
Confirm already confirmed	Domain layer	Return stable state	200	INFO	Safe	Safe
Cancel already canceled	Domain layer	Return stable state	200	INFO	Safe	Safe
Database unavailable (connection failure)	Infrastructure layer	{code: database_unavailable}	503	ERROR	Immediate retry allowed	Safe
Transaction deadlock detected	Infrastructure layer	{code: database_unavailable}	503	ERROR	Immediate retry allowed	Safe
Request timeout (server-side timeout)	API layer	{code: timeout}	504	ERROR	Safe retry	Safe
Partial transaction failure (exception during create/cancel)	Service layer	{code: internal_error}	500	ERROR	Safe retry	Atomic rollback ensures safety
Unexpected infrastructure error	Infrastructure layer	{code: internal_error}	500	ERROR	Safe retry	Safe
Malformed UUID in path parameter	Validation layer	{code: invalid_input}	422	INFO	No retry	N/A
Detailed Behavior Definitions
1️⃣ Invalid Input

Detected At:
Validation layer (FastAPI + Pydantic)

Examples:

Missing required field

quantity <= 0

Invalid UUID

User Response:
422 with stable error envelope.

Retry Strategy:
No retry unless client corrects request.

Idempotent Behavior:
Not applicable.

2️⃣ Missing Resource

Includes:

SKU not found

Reservation not found

Detected At:
Service layer

User Response:
404 with stable error code.

Retry Strategy:
Only retry if resource may later exist.

Idempotent Behavior:
Safe to retry.

3️⃣ Duplicate Submission (Idempotency)

Detected At:
Infrastructure layer (unique constraint on idempotency_key)

Behavior:
Return existing reservation deterministically.

No 409.
No second write.
No double reservation.

Retry Strategy:
Safe to retry indefinitely.

Idempotent Behavior:
Protected by DB constraint.

4️⃣ Concurrency Conflict (Insufficient Inventory)

Detected At:
Service layer via atomic conditional UPDATE rowcount.

Condition:
reserved_quantity + qty > total_quantity

User Response:
409 insufficient_inventory

Retry Strategy:
Retry only if inventory changes externally.

Idempotent Behavior:
Safe to retry.

5️⃣ Illegal State Transition

Detected At:
Domain layer.

Examples:

confirmed → canceled

canceled → confirmed

User Response:
409 illegal_state_transition

Retry Strategy:
No retry.

Idempotent Behavior:
If repeat same operation on same state → stable success.

6️⃣ Database Unavailable

Detected At:
Infrastructure layer.

Includes:

Connection failure

Pool exhaustion

Network outage

User Response:
503 database_unavailable

Retry Strategy:
Immediate retry allowed.

Idempotent Behavior:
Safe.

7️⃣ Timeout

Detected At:
API boundary or infrastructure.

User Response:
504 timeout

Retry Strategy:
Safe retry.

Idempotent Behavior:
Safe due to atomic transaction guarantees.

8️⃣ Partial Transaction

Detected At:
Service layer during transaction.

Behavior:
Transaction rolled back automatically by session.begin() context.

User Response:
500 internal_error

Retry Strategy:
Safe retry.

Idempotent Behavior:
Safe — no half-write state possible.

9️⃣ Deadlock (Postgres)

Detected At:
Infrastructure layer.

Mapped to:
503 database_unavailable

Retry Strategy:
Immediate retry allowed.

Idempotent Behavior:
Safe.

Logging Discipline

All failures:

Logged exactly once at API boundary.

Include:

request_id (if available)

reservation_id (if available)

sku (if applicable)

No secrets logged.

No SQL statement logged.

No stack trace returned to client.

Lower layers must not log failures already mapped.

Enforcement

Every endpoint maps to at least one failure scenario.

All illegal transitions are explicitly covered.

Concurrency conflict explicitly modeled.

No background job scenarios exist (intentionally out of scope).

Tests will derive directly from this matrix.