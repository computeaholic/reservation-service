.DEFAULT_GOAL := help

.PHONY: help fmt format lint typecheck precommit test coverage up down migrate rollback run scan

PYTHON ?= python3
DATABASE_URL ?= postgresql+psycopg://postgres:postgres@localhost:5432/reservation_test
COMPOSE_DATABASE_URL ?= postgresql+psycopg://postgres:postgres@postgres:5432/reservation_test

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-12s %s\n", $$1, $$2}'

fmt: ## Format code with black
	$(PYTHON) -m black .

format: ## Format code and apply safe Ruff fixes
	$(PYTHON) -m black .
	$(PYTHON) -m ruff check . --fix

lint: ## Run static quality and security checks
	$(PYTHON) -m ruff check .
	$(PYTHON) -m mypy src
	PYTHONWARNINGS=default $(PYTHON) -m bandit -r src

typecheck: ## Run mypy type checks
	$(PYTHON) -m mypy src

precommit: ## Install pre-commit hooks
	$(PYTHON) -m pre_commit install

validate-hooks: ## Run the validation hooks without branch-policy enforcement
	SKIP=block-main-branch-commit $(PYTHON) -m pre_commit run --all-files

test: ## Run Postgres-backed test suite with coverage gates
	DATABASE_URL=$(DATABASE_URL) PYTHONPATH=src $(PYTHON) -m pytest

coverage: ## Run explicit coverage command
	DATABASE_URL=$(DATABASE_URL) PYTHONPATH=src $(PYTHON) -m pytest -q -W error --cov=. --cov-report=term-missing --cov-fail-under=80

up: ## Recreate and start compose stack deterministically
	docker compose down -v --remove-orphans
	docker compose up -d postgres dev

down: ## Stop compose stack
	docker compose down --remove-orphans

migrate: ## Apply latest Alembic migration in app container
	docker compose run --rm -e DATABASE_URL=$(COMPOSE_DATABASE_URL) dev alembic upgrade head

rollback: ## Roll back one Alembic migration in app container
	docker compose run --rm -e DATABASE_URL=$(COMPOSE_DATABASE_URL) dev alembic downgrade -1

run: ## Run the full validation suite against the local Postgres database
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) validate-hooks

scan: ## Scan built image for HIGH/CRITICAL vulnerabilities
	docker build -t reservation-service:verify .
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.49.1 image --severity HIGH,CRITICAL reservation-service:verify