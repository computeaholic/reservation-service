.DEFAULT_GOAL := help

.PHONY: help fmt format lint typecheck precommit test coverage up down migrate rollback run scan

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-12s %s\n", $$1, $$2}'

fmt: ## Format code with black
	python -m black .

format: ## Format code and apply safe Ruff fixes
	python -m black .
	python -m ruff check . --fix

lint: ## Run static quality and security checks
	python -m ruff check .
	python -m mypy
	PYTHONWARNINGS=default python -m bandit -r src

typecheck: ## Run mypy type checks
	python -m mypy .

precommit: ## Install pre-commit hooks
	pre-commit install

test: ## Run Postgres-backed test suite with coverage gates
	DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/reservation_test \
	python -m pytest

coverage: ## Run explicit coverage command
	python -m pytest -q -W error --cov=. --cov-report=term-missing --cov-fail-under=80

up: ## Recreate and start compose stack deterministically
	docker compose down -v --remove-orphans
	docker compose up -d --build

down: ## Stop compose stack
	docker compose down --remove-orphans

migrate: ## Apply latest Alembic migration in app container
	docker compose run --rm app alembic upgrade head

rollback: ## Roll back one Alembic migration in app container
	docker compose run --rm app alembic downgrade -1

run: ## Run app service foreground with build
	docker compose up --build app

scan: ## Scan built image for HIGH/CRITICAL vulnerabilities
	docker build -t reservation-service:verify .
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.49.1 image --severity HIGH,CRITICAL reservation-service:verify