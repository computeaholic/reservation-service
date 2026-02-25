Constraints — reservation-service

This document defines the non-negotiable constraints for reservation-service.

Constraints exist to prevent drift, reduce ambiguity, and enforce consistency.

This repository inherits the Backend Stack Profile v1.0 and is bound by it.

1. Stack Freeze

The following stack is frozen for this repository:

Language:
Python 3.12 (pinned in pyproject.toml)

Framework:
FastAPI

Database:
PostgreSQL (Dockerized for local development)

Migration Tool:
Alembic (upgrade and downgrade required)

Testing Tools:
pytest (80–85% coverage target)

Formatting Tools:
black

Linting Tools:
ruff
mypy

CI Provider:
GitHub Actions

Containerization Strategy:
Dockerfile (pinned base image, no latest)
docker-compose (app + postgres)

Changes require:

Clear justification in TRADEOFFS.md

Alternatives considered

Impact assessment

Update to SPEC_PACK.md

Re-freeze via FREEZE.md

No silent stack changes.

2. Dependency Rules

Allowed dependencies are limited to:

FastAPI

Pydantic v2

SQLAlchemy 2.x

Alembic

psycopg (or equivalent PostgreSQL driver)

pytest

ruff

black

mypy

No additional runtime dependencies may be introduced unless:

They solve a production-relevant problem

They are documented in TRADEOFFS.md

Alternatives are considered

They do not expand scope

Explicitly prohibited:

Caching frameworks

Background task schedulers

Message brokers

Distributed lock libraries

ORM extensions that obscure SQL semantics

Experimental libraries

Dependencies must preserve clarity and transactional transparency.

3. Structural Rules
3.1 Dependency Direction

Allowed dependency flow:

api → services → domain
infrastructure → services (injected)

domain must not import:

api

services

infrastructure

config

No upward imports.
No circular dependencies.

This is binding.

3.2 Layer Isolation

Domain layer defines:

Reservation state transitions

Invariants

Domain exceptions

Services layer:

Coordinates transactions

Executes conditional updates

Orchestrates persistence

Infrastructure layer:

Database session management

ORM models

Logging configuration

API layer:

Input validation

Error envelope mapping

HTTP concerns only

No business logic in API.
No invariants in infrastructure.
No transaction logic in domain.

3.3 Folder Discipline

Required structure:

/src
  api/
  services/
  domain/
  infrastructure/
  config/
  main.py

Prohibited:

utils/

common/

helpers/

Ambiguous folder names

Every folder must have a single architectural responsibility.

3.4 Naming Conventions

snake_case for files/modules

PascalCase for classes

UPPER_SNAKE_CASE for constants

No abbreviations like inv, resv, svc

Descriptive identifiers only

Consistency is required across the entire repository.

4. Transaction Discipline

All database mutations must:

Use explicit with session.begin():

Define atomic boundaries

Avoid implicit commits

Avoid multi-step writes outside transaction scope

Reservation creation must:

Perform conditional inventory update

Insert reservation row

Fail atomically if either fails

Cancel must:

Decrement inventory

Update reservation status

Occur in one transaction

No partial writes permitted.

5. Error Handling Discipline

All errors must:

Follow the defined error envelope

Map to stable machine-readable codes

Avoid leaking stack traces

Be logged exactly once at API boundary

No silent exception swallowing.
No inconsistent error formats.
No implicit HTTP 500 without mapping.

6. Documentation Discipline

Documentation must:

Be concise and structured

Avoid marketing tone

Avoid speculative expansion

Avoid TODO placeholders

Avoid “future extensibility” sections

If ambiguity is discovered:

Stop implementation.
Update SPEC_PACK.
Re-freeze.

7. Scope Discipline

Scope is defined in SPEC_PACK.md.

This repository is intentionally limited to:

2 entities

5 endpoints

0 background processes

No feature creep permitted.

Prohibited without re-freeze:

Inventory adjustment endpoint

Batch reservations

Reservation expiration worker

Optimistic version column addition

Distributed locking

Caching

Horizontal scaling enhancements

All expansions require:

Update SPEC_PACK.md

Update TRADEOFFS.md

Update FREEZE.md

New freeze commit

Constraint precedes ambition.