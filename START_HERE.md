# Project Spec Template

This repository defines the canonical specification system used to design
software projects before implementation begins.

It is the enforcement layer for disciplined execution.

It is binding.

---

## 1. Mission

To define software systems clearly and deterministically before writing code.

This repository enforces:

- Explicit scope definition
- Explicit state modeling
- Explicit failure modeling
- Constraint freezing before coding
- Deterministic structure and naming
- Mechanical quality gates
- Clear definition of completion

Implementation is not the bottleneck.

Ambiguity is.

---

## 2. What This Repository Is

- A specification discipline framework
- A constraint and drift prevention system
- A repeatable project initialization standard
- A senior-level execution model
- A machine-ready system definition format

---

## 3. What This Repository Is Not

- A framework
- A code scaffold
- A boilerplate generator
- An AI orchestration engine
- A startup template
- A platform foundation

This repository produces bounded, defensible systems.

Nothing more.

---

## 4. Canonical Derived Project Structure

Every backend project derived from this template must contain:


/docs
SPEC_PACK.md
SCOPE.md
CONSTRAINTS.md
CONVENTIONS.md
FAILURE_MODES.md
STATE_MODEL.md (if applicable)
TESTING.md
OPERATIONS.md
TRADEOFFS.md
INTERVIEW_DEFENSE.md
SYNC_LOCK.md
FREEZE.md

/src
/tests
Makefile
pyproject.toml
Dockerfile
docker-compose.yml
.pre-commit-config.yaml
.github/workflows/ci.yml


No additional top-level folders without documented justification.

No unused folders.

No structural drift.

Derived projects may either:

- Maintain `STATE_MODEL.md`, `TESTING.md`, and `OPERATIONS.md` as separate files, OR
- Embed those sections inside `SPEC_PACK.md`.

The chosen structure must be explicitly declared in `FREEZE.md`.

Specification artifacts may be grouped under `/project_spec/` to reduce repository root clutter.
`START_HERE.md` must remain at repository root.

---

## 5. Required Order of Execution

No `/src` directory may be created until:

1. `SPEC_PACK.md` is complete.
2. Scope is defined in `SCOPE.md`.
3. Constraints are frozen in `CONSTRAINTS.md`.
4. Conventions are adopted from `CONVENTIONS.md`.
5. Failure matrix is complete in `FAILURE_MODES.md`.
6. State model is complete (if applicable).
7. Complexity budget is declared.
8. Tradeoffs are documented.
9. Interview defense is drafted.
10. `FREEZE.md` is created and committed.

No partial specification.
No placeholder logic.
No parallel coding.

Clarity precedes implementation.

---

## 6. Stack Discipline

Derived projects inherit the canonical Backend Stack Profile.

The following are frozen unless explicitly revised:

- Language
- Framework
- Database
- Migration tool
- Testing tools
- Formatting tools
- Linting tools
- CI provider
- Containerization model

Stack deviations require:

- Update to CONSTRAINTS.md
- Update to TRADEOFFS.md
- Update to SPEC_PACK.md
- Re-freeze

No silent dependency drift.

---

## 7. Structural Discipline

Derived projects must follow strict conventions:

- snake_case file names
- PascalCase classes
- UPPER_SNAKE constants
- No camelCase directories
- Clear dependency direction
- Domain isolated from infrastructure
- No dumping-ground folders (e.g., `utils`, `common`, `misc`)
- No circular imports
- No implicit transactions

Conventions are binding.

---

## 8. Failure Discipline

Every failure must define:

- Detection layer
- User-facing response
- Log level
- Retry behavior (if applicable)
- Idempotency behavior

Failures without defined behavior are design gaps.

---

## 9. Freeze Protocol

Before coding begins:

- All spec documents must be complete.
- `FREEZE.md` must record:
  - Freeze date
  - Commit hash
  - Bound artifacts

After freeze:

- Scope may not expand without revision.
- Dependencies may not change silently.
- Complexity budget may not expand without re-freeze.
- No TODO placeholders allowed.

Ambiguity discovered during implementation requires:
Pause → Update docs → Re-freeze.

---

## 10. Mechanical Quality Gates

Derived projects must enforce:

- No direct push to main
- Pull request required
- Pre-commit hooks (format, lint, typecheck, test)
- CI required and enforced
- 80–85% test coverage target
- Deterministic Makefile targets

No bypasses.

---

## 11. Operating Philosophy

- Clarity over cleverness.
- Constraint over ambition.
- Determinism over intuition.
- Completion over expansion.
- Explicit tradeoffs over implied assumptions.
- Correctness before scale.

Every derived project must reflect disciplined execution.

This template exists to prevent drift.