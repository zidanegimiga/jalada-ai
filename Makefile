COMPOSE := docker compose -f infra/docker-compose.yml $(if $(wildcard .env),--env-file .env)

.PHONY: up down logs check format

# Build and start the whole stack in the background.
up:
	$(COMPOSE) up --build --detach --wait

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs --follow

# Lint, type check and test everything, the same way CI does.
check:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy
	uv run --directory apps/api pytest
	uv run --directory apps/worker pytest
	cd apps/web && npm run lint && npm run typecheck && npm test

format:
	uv run ruff format .
	uv run ruff check --fix .
