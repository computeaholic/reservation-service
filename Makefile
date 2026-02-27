.PHONY: fmt lint typecheck test coverage up down migrate rollback run scan

fmt:
	python -m black .

lint:
	python -m ruff check .

typecheck:
	python -m mypy .

test:
	python -m pytest -q -W error

coverage:
	python -m pytest -q -W error --cov=. --cov-report=term-missing --cov-fail-under=80

up:
	docker compose up -d --build

down:
	docker compose down --remove-orphans

migrate:
	docker compose run --rm app alembic upgrade head

rollback:
	docker compose run --rm app alembic downgrade -1

run:
	docker compose up --build app

scan:
	docker build -t reservation-service:verify .
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.49.1 image --severity HIGH,CRITICAL reservation-service:verify