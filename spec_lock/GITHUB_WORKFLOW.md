GitHub Workflow — reservation-service

This document is binding for this repository.

This repository enforces predictable, auditable, low-friction engineering workflow.

1. Branching Model

Default branch: main

Direct pushes to main are prohibited.

All changes require Pull Request.

Required checks must pass before merge.

Branch naming:

feature/<short-description>

fix/<short-description>

chore/<short-description>

refactor/<short-description>

docs/<short-description>

No long-lived feature branches.
Branches should be short, focused, and reviewable.

2. Commit Format

Commits must be structured and atomic.

Format:

type: concise description

Examples specific to this repository:

feat: implement atomic inventory reservation update

fix: enforce rollback on reservation failure

refactor: isolate reservation domain transitions

docs: complete failure matrix

chore: pin python base image version

freeze: specification v1.0 locked

Rules:

One logical change per commit.

No “misc changes”.

No large unreviewable commits.

No mixing refactor and feature work.

Freeze commit must be separate and clearly identifiable.

Migration changes must be isolated from unrelated logic changes.

3. Pull Request Rules

Each PR must:

Link to the relevant section in SPEC_PACK.md.

Explain what changed.

Explain why it was necessary.

Confirm tests were updated or added.

Confirm no scope expansion (or explicitly state expansion and spec update).

PR description must answer:

What changed?

Why was this necessary?

What failure modes are impacted?

Does this alter the complexity budget?

Does this modify transaction boundaries?

Does this modify concurrency model?

If yes to any structural change:
Spec update + re-freeze required.

No PR without explanation.

4. CI Requirements

CI must enforce:

ruff (lint)

black --check

mypy

pytest

Coverage threshold: 80–85% (defined in SPEC_PACK)

CI must fail on:

Formatting errors

Lint errors

Type errors

Failing tests

Coverage below threshold

Required checks must block merge.

No manual bypass of required checks.

5. Freeze Commit Protocol

When specification is frozen:

Commit message must be:

freeze: specification v1.0 locked

Requirements:

FREEZE.md must include commit hash.

No implementation commits may precede freeze commit.

/src directory must not exist before freeze commit.

If specification changes:

Commit message must be:

refreeze: specification vX.Y updated

Freeze is binding.
It is not symbolic.

6. Reproducibility

A clean clone must allow:

make up
make migrate
make test

Without undocumented steps.

The following must be deterministic:

Python version

Dependency versions

Docker base image

Database version

Migration state

No hidden setup steps.
No local-only assumptions.
No manual DB manipulation required.