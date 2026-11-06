# 0020. Feature modules

Status: Accepted
Date: 2026-11-06

## Context
The API was grouped by layer: `domain`, `application`, `adapters`, `api` and `pipeline`. One feature, such as Telegram, was spread over about ten files in six folders, and every feature added to the same central files: `ports.py`, `tables.py`, the list of routers and the list of services. Those files had grown past the 200-line limit, and nothing stopped one feature from reaching into another's tables.

## Options considered
1. **Keep the layers, split the big files.** Smaller files, but a feature is still spread across the package.
2. **Feature modules, each with the same layers inside.** A feature lives in one folder; the layering that keeps business rules free of vendors stays.
3. **Separate services.** Far more to run and deploy than the product needs.

## Decision
Option 2.

```
jalada/
  core/       infrastructure any module can use: settings, logging, clock, database base,
              jobs, storage client, health checks, error tracking
  shared/     small helpers with no infrastructure: application errors, money, dates, HTTP
  modules/
    accounts/ evidence/ pipeline/ ledger/ exports/ telegram/ health/
      domain/       pure rules, no input or output
      application/  use cases, and ports.py with the interfaces they need
      adapters/     implementations of the ports, and tables.py for the module's tables
      api/          routes and request and response schemas
      module.py     the module's routers
  app.py, composition.py, services.py, unit_of_work.py, sql_unit_of_work.py, tables.py
              the pieces that bring the modules together
  migrations/ Alembic, seeing every module's tables through tables.py
```

Rules, checked in continuous integration with import-linter:
- `core` and `shared` never import a module or the pieces at the top.
- In every module, `domain` imports no other layer and no vendor library.
- Inside a module, layers only depend downwards: `module.py`, then `api` or `adapters`, then `application`, then `domain`.
- A module may use another module's `domain`, `application` and response schemas, never its `adapters` or routes. One exception is listed in the contract: finding evidence nobody has entered yet joins the evidence and entries tables.
- The cross-module rule checks direct imports only for now, because every route reaches the other modules indirectly through the shared `Services`.

To add a feature: create `modules/<name>/` with the four layers and `module.py`, add the module to the list in `app.py`, add its tables to `tables.py`, then run `make migration name="..."` and `make check`.

## Consequences
- A feature can be read, reviewed and removed as one folder.
- The API's behaviour did not change: the OpenAPI contract in `apps/api/openapi.json` and every test stayed the same through the move.
- One unit of work still opens repositories for every module, and routes still get their use cases from one shared `Services`. Giving each module its own transaction and its own services is a later step; it changes every use case and fake but not this layout.
