# Working on Jalada AI

## The product
Jalada AI keeps money records for Kenyans with no accountant. A user sends a receipt photo, a PDF or a forwarded M-Pesa message. A pipeline works out what the money was for, categorises it, keeps the evidence and saves it to a ledger. The ledger feeds a monthly view of money in and out and, at filing time, figures grouped the way the Kenya Revenue Authority's iTax return asks for them.

Users have scattered income, many small payments, and often small or basic phones.

## How changes are made
1. **Plan first.** Write down what a change will do before writing it.
2. **One slice per commit.** Each commit is one complete, working piece with its tests, for example sign-up and sign-in end to end. Refactors go in commits of their own. Work happens on `dev` and reaches `main` through pull requests.
3. **Decisions get a record.** Every library, service, data store or pattern gets a record in `docs/adr/` before it lands in code. No new dependency without one.
4. **Tests come with code.** Every change in behaviour ships with tests, and `make check` passes before anything is committed.
5. **No guessing about tax.** Tax facts come from `docs/domain/`, checked against the Kenya Revenue Authority.

## Architecture
- **Ports and adapters.** Business logic depends on interfaces (ports), never on vendor libraries. Each vendor sits behind an adapter. Swapping a provider means one new adapter and one configuration change.
- **Dependency injection.** Each app wires adapters into use cases in one composition root. No global singletons, no clients created inside functions.
- **Feature modules.** The API is split by feature under `jalada/modules/` (accounts, evidence, pipeline, ledger, exports, telegram, health). Each module has the same layers: `domain` holds pure rules with no input or output, `application` holds use cases and the ports they need, `adapters` implements those ports, and `api` holds thin routes and schemas that only call use cases. `jalada/core/` holds infrastructure any module can use, and `jalada/shared/` small helpers; neither imports a module. Modules may use each other's domain and application code, never another module's adapters or tables. Decision 0020 explains the layout and how to add a module.
- **Configuration** comes from the environment and is validated at startup. No secrets in code, logs or tests.

## Size and naming
- Functions under about 30 lines, files under about 200, React components under about 150. Split before adding more.
- Names say what a thing is or does. No abbreviations except widely known ones.
- Python: `snake_case` functions and variables, `PascalCase` classes, `snake_case.py` files.
- TypeScript: `camelCase` and `PascalCase`, `kebab-case.tsx` files.
- One responsibility per module. If describing it needs the word "and", split it.

## Security
- All financial data is personal data under Kenya's Data Protection Act.
- Follow the OWASP Top 10 (the Open Worldwide Application Security Project's list of common web risks).
- Validate every input with a schema. Parameterised queries only. Rate limit sign-in and upload routes.
- Check upload type and size. Never trust a file name.
- Argon2 for passwords. Sessions in secure, HTTP-only cookies. Every query is scoped to the signed-in user in one place.
- Encrypt evidence at rest, and serve it only to its owner, through the API.
- Never store an M-Pesa statement password. Never log raw financial content.
- Users can export and delete all their data.

## Product rules that never bend
- The pipeline never decides on its own that something is taxable or deductible. Unclear items go to the review queue.
- Raw evidence is permanent. Every ledger entry links to its original evidence and to the run that produced it.
- The database is the source of truth. Exports are generated views, never edited back in.

## Testing
- Backend: pytest. Unit tests for the domain, use case tests with fake adapters, a few integration tests against real Postgres in Docker.
- Frontend: Vitest with Testing Library, and Playwright for the main journeys.
- Pipeline: the evaluation suite in `evals/`, run in continuous integration with pass thresholds.
- Test data is always invented. Never commit real receipts, statements, certificates, `.env` files or keys.

## Writing style
Docs use short, plain sentences. No em dashes and no emojis. Spell out every acronym the first time and say what it means.

## Where things are
- `apps/api`: the FastAPI service and the `jalada` package: `core/`, `shared/`, `modules/`, and at the top the pieces that bring the modules together (`app.py`, `composition.py`, `services.py`, `unit_of_work.py`, `tables.py`). `apps/worker`: runs pipeline jobs. `apps/web`: the Next.js app.
- `docs/adr/`: decisions. `docs/design/`: design documents. `docs/domain/`: notes on Kenyan tax, M-Pesa messages and withholding certificates, to verify rather than treat as tax advice.
- `evals/`: invented fixtures and the pipeline scoring script. `infra/`: docker compose.
