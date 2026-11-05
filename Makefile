COMPOSE := docker compose -f infra/docker-compose.yml $(if $(wildcard .env),--env-file .env)

.PHONY: up down logs db migrate migration check test-integration format

# Build and start the whole stack in the background.
up:
	$(COMPOSE) up --build --detach --wait

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs --follow

# Start only Postgres, on localhost:5433, for running the apps or tests outside Docker.
db:
	$(COMPOSE) up --detach --wait postgres

migrate: db
	uv run --env-file .env jalada-migrate

# make migration name="add evidence"
migration: db
	uv run --env-file .env jalada-migrate revision "$(name)"

# Lint, type check and test everything, the same way CI does.
check:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy
	uv run --directory apps/api pytest
	uv run --directory apps/worker pytest
	cd apps/web && npm run lint && npm run typecheck && npm test

# Repository tests against the real database in docker compose.
test-integration: db
	JALADA_TEST_DATABASE_URL=postgresql+psycopg://jalada:jalada@localhost:5433/jalada_test \
		uv run --directory apps/api pytest -m integration

format:
	uv run ruff format .
	uv run ruff check --fix .
