COMPOSE := docker compose -f infra/docker-compose.yml $(if $(wildcard .env),--env-file .env)

.PHONY: up up-ollama ollama-model down logs db migrate migration check test-integration format

# Build and start the whole stack in the background.
up:
	$(COMPOSE) up --build --detach --wait

# The same stack plus a local language model server on localhost:11434.
up-ollama:
	$(COMPOSE) --profile ollama up --build --detach --wait

# Download the default local vision model (about 3 GB) into the ollama container.
OLLAMA_MODEL ?= qwen2.5vl:3b
ollama-model:
	$(COMPOSE) --profile ollama exec ollama ollama pull $(OLLAMA_MODEL)

down:
	$(COMPOSE) --profile ollama down

logs:
	$(COMPOSE) logs --follow

# Start only Postgres (localhost:5433) and storage (localhost:8333), for work outside Docker.
db:
	$(COMPOSE) up --detach --wait postgres storage

migrate: db
	uv run --env-file .env jalada-migrate
	uv run --env-file .env jalada-setup-storage

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
	uv run python evals/run_evals.py
	cd apps/web && npm run lint && npm run typecheck && npm test

# Repository tests against the real database in docker compose.
test-integration: db
	JALADA_TEST_DATABASE_URL=postgresql+psycopg://jalada:jalada@localhost:5433/jalada_test \
	JALADA_TEST_S3_ENDPOINT=http://localhost:8333 \
		uv run --directory apps/api pytest -m integration

format:
	uv run ruff format .
	uv run ruff check --fix .
