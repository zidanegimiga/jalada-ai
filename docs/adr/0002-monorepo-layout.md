# 0002. One repository with separate apps

Status: Accepted
Date: 2026-11-04

## Context
Jalada AI has three running parts: an HTTP API in Python, a background worker that runs the agent pipeline, and a Next.js web app. The worker needs the same domain rules, ports and adapters as the API. The web app needs the API's request and response shapes, which it will get from a typed client generated from the API's OpenAPI schema (a machine-readable description of every endpoint). One person reviews every change, so a change that touches the API and the screen should be reviewable as one unit.

## Options considered
1. **Separate repositories for API, worker and web.**
   Pros: each app has its own history and pipeline.
   Cons: the worker would need the API code published as a package or copied. A change to an endpoint and its screen becomes two pull requests that must land in step. More setup for one owner.
2. **One repository, with the worker inside the API package.**
   Pros: fewest folders.
   Cons: the worker and the API start differently, scale differently and get separate Docker images. Mixing them hides that boundary.
3. **One repository with `apps/api`, `apps/worker` and `apps/web`, plus shared top-level folders.**
   Pros: one history and one review for cross-cutting changes. The worker imports the `jalada` package from `apps/api` directly. Each app still has its own dependencies, Dockerfile and tests.
   Cons: continuous integration must run only the checks relevant to the changed app, or it gets slow. Tooling for Python and Node lives side by side.
4. **Option 3 plus a monorepo build tool such as Turborepo or Nx.**
   Pros: task caching and dependency graphs between apps.
   Cons: another tool to learn and configure, built mainly for JavaScript. With two languages and three apps, the gain is small.

## Decision
Option 3. One repository laid out as below, with a root Makefile for common commands instead of a monorepo build tool.

```
jalada-ai/
├── AGENTS.md, CLAUDE.md, README.md
├── .claude/skills/       project skills, local only and never committed
├── apps/
│   ├── api/              FastAPI service, owns the jalada Python package
│   ├── worker/           runs pipeline jobs, imports jalada from apps/api
│   └── web/              Next.js app
├── evals/                invented fixtures, expected outputs, scoring scripts
├── docs/                 design, adr, domain
├── infra/                docker compose, deployment config
└── .github/workflows/    continuous integration
```

Inside `apps/api/src/jalada/`, code is split into `domain`, `application`, `adapters`, `pipeline`, `api`, `config` and `composition.py`, as `AGENTS.md` describes.

## Consequences
- A feature that spans the API and the web app lands as one reviewable change.
- The worker and the API cannot drift apart, because they share one package.
- Continuous integration uses path filters so a web-only change does not run the Python checks, and the other way round.
- The Dockerfiles live with each app and are wired together from `infra/`.
- If the project grows past what a Makefile handles, revisit option 4 in a new record.
