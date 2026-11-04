# 0004. FastAPI and Uvicorn for the HTTP API

Status: Accepted
Date: 2026-11-04

## Context
The API serves the web app and receives Telegram webhooks. Every request and response must be validated against a schema. The web app's typed client is generated from an OpenAPI schema (a machine-readable description of every endpoint), so the framework should produce one. Settings and adapters must be passed in through a composition root, not imported globally.

## Options considered
1. **Django with Django REST Framework.** Batteries included, with an admin site and its own object-relational mapper (ORM, the layer that maps tables to classes). Its models pull the database into the domain, which works against ports and adapters, and schema generation needs extra packages.
2. **Flask.** Small and familiar. No built-in validation, typing or OpenAPI, so we would add and wire several extensions ourselves.
3. **Litestar.** Typed and fast, with OpenAPI built in. A smaller community, and fewer answers when something goes wrong.
4. **FastAPI.** Validation through Pydantic, which we already use for settings. OpenAPI and interactive docs come for free. Dependency injection is built in. Widely used for model-serving and AI work.

For the server that runs the app:
1. **Uvicorn.** The standard server for ASGI apps (Asynchronous Server Gateway Interface, the Python standard for async web apps). Small and well maintained.
2. **Hypercorn or Granian.** Capable alternatives with fewer users.

## Decision
FastAPI, served by Uvicorn. The app is built by a factory function, `create_app(settings)`, called from the composition root. Interactive docs and the OpenAPI schema are served outside production only. In tests, FastAPI's test client runs on httpx2, the HTTP client Starlette (the toolkit FastAPI is built on) now expects.

## Consequences
- Request and response schemas live next to routes as Pydantic models and appear in the OpenAPI schema automatically.
- Hiding docs in production removes a map of our endpoints from public view. The web app's client is generated at build time from a non-production instance.
- FastAPI moves quickly between minor versions. The lockfile pins it, and Dependabot proposes upgrades we can review.
