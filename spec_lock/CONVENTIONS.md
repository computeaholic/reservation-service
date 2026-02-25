# Conventions

This document defines project conventions that are binding for any repository
derived from this template.

Conventions exist to enforce predictability and reduce review overhead.

---

## 1. Repository Structure

Backend repositories must use the following structure:

/
  START_HERE.md
  README.md
  /docs
  /src
    api/
    domain/
    services/
    infrastructure/
    config/
    main.py
  /tests
  Makefile
  pyproject.toml
  Dockerfile
  docker-compose.yml
  .pre-commit-config.yaml
  .github/workflows/ci.yml

Rules:
- No extra top-level folders without documented justification.
- No unused folders.
- No “misc” buckets.
 - Maximum abstraction layers: 3 (api → services → domain)

---

## 2. Dependency Direction

Allowed direction:

- api → services → domain
- infrastructure → services (injected)
- config may be imported by api/services/infrastructure (project-specific)
- domain must not import api/services/infrastructure/config

Rules:
- No upward imports.
- No circular dependencies.
- Domain must remain framework-agnostic.

---

## 3. Naming Conventions

Files and modules:
- snake_case filenames
- snake_case module names
- No camelCase directories

Classes:
- PascalCase

Constants:
- UPPER_SNAKE_CASE

Identifiers:
- Prefer explicit names over abbreviations.
- Avoid single-letter names except small local scopes.

---

## 4. API Conventions

Error envelope (required everywhere):

{
  "error": {
    "code": "machine_identifier",
    "message": "human readable"
  }
}

Rules:
- No raw exception details returned to clients.
- Error codes are stable and documented.
- All endpoints must document expected error codes.
 - Error mapping must occur at the API boundary layer only.

---

## 5. Database and Migrations

Rules:
- All schema changes require Alembic migrations.
- Downgrade paths must exist.
- No schema drift between models and DB.

Transaction discipline:
- All mutations must use explicit transaction boundaries.
- No implicit commits.
- No hidden side effects.

---

## 6. Idempotency and Conflicts

Rules:
- Any create/submit operation that can be duplicated must define idempotency behavior.
- Prefer DB constraints for dedupe/uniqueness.
- IntegrityError must be mapped deterministically (typically 409) with a stable error code.

---

## 7. Logging

Rules:
- Structured logging only.
- No print statements.
- Do not log secrets.
- Errors are logged once at the boundary layer (avoid duplicate logs).
- Log messages must include enough context to debug (IDs, key fields), without PII leakage.

---

## 8. Testing

Requirements:
- pytest is required.
- Tests must derive from:
  - Failure matrix (FAILURE_MODES.md)
  - State model (STATE_MODEL.md)
- Illegal state transitions must be tested.
- Concurrency tests required when concurrency model exists.
- Coverage target: 80–85%.

Rules:
- Avoid overly-mocked tests.
- Prefer integration tests for API + DB behavior where appropriate.
- Tests must be deterministic (no flakey timing assumptions).

---

## 9. Tooling and Quality Gates

Required tools (backend profile):
- ruff
- black
- mypy
- pytest
- pre-commit
- GitHub Actions CI

Rules:
- No direct push to main.
- PR required.
- CI must pass (lint/type/test) before merge.
- Required checks must not be bypassed.

No TODO stubs in finished projects.

---

## 10. Makefile Targets

Each repo must provide these targets (names consistent across repos):

make fmt
make lint
make typecheck
make test
make test-cov
make up
make down
make run
make migrate
make rollback

Rules:
- Targets must work from a clean checkout.
- Targets must be documented in README/OPERATIONS.md.

---

## 11. Version Pinning

Rules:
- Dependencies are pinned in pyproject.toml (no floating major versions).
- Docker base images must not use `latest`.
- Tool versions should be stable and reproducible.

---

Conventions are binding. If a convention must change, document the reason in
TRADEOFFS.md, update the Spec Pack, and re-freeze.