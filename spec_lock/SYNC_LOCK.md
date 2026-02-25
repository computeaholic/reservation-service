SYNC LOCK — reservation-service

This document captures the authoritative mission and boundaries of this repository.

It mirrors the original ultra-dense sync message used to initialize the project.

This file exists to prevent context drift.

It is binding.

1. Project Identity

Repository Name:
reservation-service

Primary Objective:
Build a reliability-focused inventory reservation service that demonstrates deterministic concurrency control, idempotency, atomic transactions, and database-enforced correctness under contention.

This repository is intentionally constrained.

It is NOT:

A platform

A startup foundation

A distributed system

A feature playground

A demo scaffold

A technology showcase

It exists to demonstrate senior-level engineering discipline.

2. Core Demonstrations (Non-Negotiable)

This repository must clearly demonstrate:

Explicit state modeling (Reservation lifecycle)

Explicit failure modeling (complete failure matrix)

Deterministic error handling (stable error envelope)

Transaction discipline (with session.begin():)

Concurrency discipline (atomic conditional update)

Idempotency on create and state transitions

Clean architectural boundaries (api → services → domain)

Mechanical CI enforcement (lint, type, test, coverage)

Operational clarity (migrations, health checks, dockerized Postgres)

These demonstrations define success.

They may not be removed without updating SPEC_PACK.md and FREEZE.md.

3. Stack Lock

This repository inherits the canonical Backend Stack Profile v1.0.

The following are frozen unless explicitly revised:

Language: Python 3.12 (pinned)

Framework: FastAPI

Database: PostgreSQL (Docker)

Migration tool: Alembic

Testing stack: pytest

Formatting/linting tools: ruff, black, mypy

CI provider: GitHub Actions

Containerization approach: Dockerfile + docker-compose

Stack changes require:

Update to CONSTRAINTS.md

Update to TRADEOFFS.md

Update to SPEC_PACK.md

Freeze revision

No silent drift.

Dependency direction defined in CONVENTIONS.md is binding and may not be altered without formal re-freeze. Layer boundaries and dependency flow are locked upon freeze.

4. Scope Guard

The scope defined in SPEC_PACK.md is binding.

This service includes:

Create reservation (idempotent)

Retrieve reservation

Confirm reservation (idempotent)

Cancel reservation (idempotent)

View inventory

It explicitly excludes:

Auth / RBAC

Payments

Multi-warehouse support

Background expiration

Distributed locking

Eventing

Caching

Horizontal scaling claims

No features may be added without:

Updating SPEC_PACK.md

Updating TRADEOFFS.md

Updating FREEZE.md

New commit hash recorded

No implicit expansion.

No “just this one improvement.”

5. Complexity Budget

The complexity budget defined in SPEC_PACK.md is binding.

Budget includes:

Maximum endpoints: 5

Maximum entities: 2 (InventoryItem, Reservation)

Maximum background processes: 0

Maximum abstraction layers: 3

Target LOC range: ~2.5–3.5k natural

No generic repository pattern

No abstraction theater

Exceeding the budget requires formal revision and re-freeze.

Constraint precedes ambition.

6. Implementation Discipline

No implementation in /src may contradict:

State model (active → confirmed / canceled)

Failure matrix

Transaction model (explicit boundaries only)

Concurrency model (atomic conditional UPDATE)

Error envelope contract

Idempotency policy (unique idempotency_key)

Stack constraints

If implementation reveals ambiguity:

Stop.
Update SPEC_PACK.md.
Revise documents.
Re-freeze.

7. Enforcement

This document functions as a boundary contract.

All engineering decisions must remain consistent with this file.

If drift occurs:

Pause development

Correct documentation

Re-freeze before continuing

This repository is judged on clarity, correctness, and constraint discipline.