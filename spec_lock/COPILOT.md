Copilot / AI Usage Policy — reservation-service

This document is binding for this repository.

This repository may use AI assistance.

AI operates under constraint.

1. AI May

AI assistance may:

Implement modules explicitly defined in SPEC_PACK.md.

Generate request/response models consistent with the defined API contract.

Implement the atomic conditional inventory update defined in the concurrency model.

Implement domain state transitions exactly as defined.

Generate tests directly derived from:

The failure matrix

The state model

The concurrency model

Suggest refactors that do not alter architecture.

Improve formatting, typing, and readability.

Generate Docker, CI, and migration scaffolding consistent with the frozen stack.

AI must operate within the frozen scope.

2. AI May Not

AI must not:

Expand scope.

Invent new architecture layers.

Introduce new dependencies without updating CONSTRAINTS.md and TRADEOFFS.md.

Add background processes (expiration workers, schedulers, etc.).

Modify the state model.

Modify transaction boundaries.

Modify the concurrency model.

Replace atomic conditional updates with optimistic locking.

Introduce distributed locking.

Introduce implicit transaction behavior.

Add repository patterns or abstraction layers not defined in spec.

Modify the error envelope contract.

Add caching.

Add authentication or RBAC.

Add foreign keys or relational constraints not documented in spec.

Any such change requires documentation update and re-freeze.

3. AI Guardrails

Before accepting AI-generated code, verify:

It aligns exactly with SPEC_PACK.md.

It respects dependency direction defined in CONVENTIONS.md.

No new dependencies were introduced.

All transaction boundaries use with session.begin():.

No implicit commits exist.

Atomic conditional update logic remains intact.

Illegal state transitions raise explicit domain exceptions.

Error responses follow the defined error envelope.

No silent error handling was added.

Logging occurs only once at API boundary.

No abstraction theater was introduced.

If ambiguity is discovered:

Stop.
Update documentation.
Re-freeze if required.

4. Human Responsibility

The engineer remains responsible for:

Architectural integrity.

Correct enforcement of the invariant:
reserved_quantity <= total_quantity.

Concurrency safety under contention.

Idempotency guarantees.

Transactional atomicity.

Failure modeling correctness.

Operational clarity.

Enforcement of complexity budget.

CI enforcement integrity.

AI accelerates implementation.

It does not own correctness.