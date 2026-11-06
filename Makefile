COMPOSE := docker compose -f infra/docker-compose.yml $(if $(wildcard .env),--env-file .env)

.PHONY: up up-ollama up-telegram ollama-model down logs db migrate migration check test-integration e2e openapi web-types format

# Build and start the whole stack in the background.
up:
	$(COMPOSE) up --build --detach --wait

# The same stack plus a local language model server on localhost:11434.
up-ollama:
	$(COMPOSE) --profile ollama up --build --detach --wait

# The stack plus the Telegram bot, reading messages by polling.
up-telegram:
	$(COMPOSE) --profile telegram up --build --detach --wait

# Download the default local vision model (about 3 GB) into the ollama container.
OLLAMA_MODEL ?= qwen2.5vl:3b
ollama-model:
	$(COMPOSE) --profile ollama exec ollama ollama pull $(OLLAMA_MODEL)

down:
	$(COMPOSE) --profile ollama --profile telegram down

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
	uv run lint-imports
	uv run --directory apps/api pytest
	uv run --directory apps/worker pytest
	uv run python evals/run_evals.py
	cd apps/web && npm run lint && npm run typecheck && npm test

# Repository tests against the real database in docker compose.
test-integration: db
	JALADA_TEST_DATABASE_URL=postgresql+psycopg://jalada:jalada@localhost:5433/jalada_test \
	JALADA_TEST_S3_ENDPOINT=http://localhost:8333 \
		uv run --directory apps/api pytest -m integration

# After changing the API on purpose: rewrite apps/api/openapi.json, which a test compares
# with the running code.
openapi:
	uv run --directory apps/api jalada-openapi
	$(MAKE) web-types

# The web app's API types, generated from apps/api/openapi.json. CI fails if they are stale.
web-types:
	cd apps/web && npm run types

# The main journey in a browser, against a separate, throwaway copy of the whole stack.
# Its own project name keeps your local data out of it. Stop your stack first (make down):
# both use the same ports.
E2E_COMPOSE := docker compose -p jalada-e2e -f infra/docker-compose.yml
e2e:
	$(E2E_COMPOSE) up --build --detach --wait
	cd apps/web && npx playwright install chromium && npm run e2e; \
		status=$$?; cd ../.. && $(E2E_COMPOSE) down --volumes; exit $$status

format:
	uv run ruff format .
	uv run ruff check --fix .
