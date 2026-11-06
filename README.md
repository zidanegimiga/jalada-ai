# Jalada AI

Jalada AI keeps money records for people in Kenya who don't have an accountant.

You send it a receipt photo, a PDF or a forwarded M-Pesa message. It works out what the money was for (business or personal, earned income or support from family, a work cost or a household cost), puts it in a category, keeps the original as evidence and saves it to a ledger. Over the month that ledger shows where your money went. At filing time it gives you the figures grouped the way the KRA iTax return asks for them.

## Why I'm building it

In 2025 I was salaried for part of the year, freelanced for the rest, had clients deduct withholding tax, and got support from family between jobs. When it came to filing my return, I had to rebuild the whole year from bank and M-Pesa statements and work out which deposits were income and which weren't. Receipts and withholding certificates were spread across email, WhatsApp and paper.

A lot of people are in the same position: mixed income, many small payments, money for the business and for the house going through the same M-Pesa line, and often a small phone with little data. Jalada AI is meant to make keeping records take seconds, and make filing time boring.

A few rules the product sticks to:

- It never decides on its own that something is taxable or deductible. Anything it is unsure about goes to a review queue, and you confirm or correct it with one tap.
- Every ledger entry links back to the original receipt, message or file, and to how it was categorised.
- Financial data is personal data under the Data Protection Act. You can export or delete everything.

## How it will work

Every piece of evidence goes through a short pipeline:

1. **Detect** what it is: an M-Pesa message, a statement, a receipt photo, a withholding certificate, a payslip or free text.
2. **Extract** the date, amount, counterparty, reference and any tax amounts. Fixed formats like M-Pesa messages are parsed with rules. OCR and a language model are only used when rules can't cope.
3. **Classify** the purpose and category, checking your own past choices for that counterparty first.
4. **Verify** the result: valid fields, amounts that add up, a plausible date, no duplicate M-Pesa code, and enough confidence. Anything that fails goes to review.

Each run records its steps, timings and model usage, so any entry can be traced back to its evidence. The scoring script in [`evals/`](evals/) runs the pipeline over invented fixtures and fails CI if accuracy drops.

## Status

Early. You can create an account with email or Google, upload receipts and PDFs, and paste M-Pesa messages. M-Pesa messages and withholding certificates are read with rules, photos with Tesseract, and anything else with a language model when one is set up. Each proposed entry is confirmed or corrected with one tap, and every choice teaches the classifier for next time. Confirmed entries make up the ledger and the monthly view of money in and out, split between business and personal, and can be downloaded as an Excel workbook for one tax year, grouped the way the iTax return asks. Receipts and messages can also be sent through a Telegram bot. You can download everything held about you, originals included, or delete your account and all of it. It is set up to run on free hosting.

## Stack

| Part | Tools |
| --- | --- |
| API and worker | Python 3.12, FastAPI, Pydantic, uv |
| Web app | Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui with Base UI |
| Reading evidence | pdfplumber, Tesseract, Gemini or Ollama behind one interface |
| Tests | pytest, Vitest, Testing Library |
| Quality | ruff, mypy (strict), ESLint, pip-audit, npm audit, gitleaks |
| Storage | PostgreSQL, S3-compatible object storage (SeaweedFS locally), evidence encrypted with AES-GCM |
| Running it | Docker, docker compose, GitHub Actions |

Every one of these choices has a short decision record in [`docs/adr/`](docs/adr/) explaining what else was considered and why.

## Project layout

```
jalada-ai/
├── apps/
│   ├── api/                  FastAPI service, home of the jalada Python package
│   │   ├── src/jalada/
│   │   │   ├── domain/       business rules, no input or output
│   │   │   ├── application/  use cases and the interfaces (ports) they need
│   │   │   ├── adapters/     database, storage, model and OCR implementations
│   │   │   ├── pipeline/     detector, extractor, classifier, verifier, runner
│   │   │   ├── api/          HTTP routes and schemas
│   │   │   ├── config/       typed settings from the environment
│   │   │   └── composition.py  wires everything together
│   │   └── tests/
│   ├── worker/               runs pipeline jobs, reuses the jalada package
│   └── web/                  Next.js app
│       └── src/
│           ├── app/          routes
│           ├── components/ui/  shadcn components
│           └── lib/          shared helpers
├── evals/                    invented fixtures and the pipeline scoring script
├── infra/                    docker compose
├── docs/
│   ├── adr/                  decision records
│   ├── design/               design documents
│   └── domain/               notes on Kenyan tax and M-Pesa
├── .github/                  CI workflows and Dependabot
├── AGENTS.md                 conventions for working in this repo
├── Makefile                  common commands
└── pyproject.toml            Python workspace and tool settings
```

The backend follows ports and adapters. Business logic only talks to interfaces, and each outside service (database, storage, model provider) sits behind an adapter, so swapping a provider means writing one adapter and changing one line in `composition.py`.

## Running it

You need [Docker](https://www.docker.com/), [uv](https://docs.astral.sh/uv/) and Node 24.

Start everything:

```bash
make up
```

The API is on http://localhost:8000 (docs at `/docs`) and the web app is on http://localhost:3000. Postgres is on port 5433 and S3 storage on port 8333. Stop it with `make down`.

Settings come from environment variables prefixed with `JALADA_`. `.env.example` lists every one with its local value; copy it and edit:

```bash
cp .env.example .env
```

### Reading photos and unfamiliar messages

Fixed formats (M-Pesa messages, withholding certificates) are read with rules. Photos go through Tesseract first. When neither works, a language model reads the evidence, if one is set up. Without one, that evidence simply waits for review.

To use a local model with Ollama (about 3 GB to download):

```bash
make up-ollama
make ollama-model
```

Then set `JALADA_MODEL_PROVIDER=ollama` in `.env` and run `make up-ollama` again. For Gemini, set `JALADA_MODEL_PROVIDER=gemini` and `JALADA_GEMINI_API_KEY`.

Free tiers and local models are only for invented data. In production the app refuses to start with a model until `JALADA_MODEL_ALLOWED_FOR_REAL_DATA=true`, which should only be set for a provider whose terms exclude training on what it is sent.

### Deploying

The API is described for Render in [`render.yaml`](render.yaml), and the web app for Netlify in [`netlify.toml`](netlify.toml). Every production setting, and what it is for, is listed in [`.env.production.example`](.env.production.example), in the same order as the local [`.env.example`](.env.example). Real values live only in the hosts' settings.

The API answers two health checks, neither needing a session. `/health` only says the process is up, and is what Render polls. `/health/ready` also checks that the database and the evidence bucket answer, returning 503 and the name of whatever failed; point uptime monitors at it. Both report the running version.

### Telegram bot

People can send receipts, PDFs and forwarded M-Pesa messages to a Telegram bot instead of the web app.

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy its token.
2. Put `JALADA_TELEGRAM_BOT_TOKEN` and `JALADA_TELEGRAM_BOT_USERNAME` (without the @) in `.env`.
3. Run `make up-telegram`. Locally the bot reads messages by polling, so no public address is needed.
4. In the app, tap Link Telegram and open the link it gives you.

Once deployed, set `JALADA_TELEGRAM_WEBHOOK_SECRET` to a long random value and run `jalada-telegram set-webhook`, so Telegram calls the app instead.

### Google sign-in

Google sign-in is off until you give it credentials:

1. In the [Google Cloud console](https://console.cloud.google.com/apis/credentials), create an OAuth client ID of type "Web application".
2. Add `http://localhost:3000/v1/auth/google/callback` as an authorised redirect URI.
3. Put the client ID and secret in `.env` as `JALADA_GOOGLE_CLIENT_ID` and `JALADA_GOOGLE_CLIENT_SECRET`, then run `make up` again.

`make up` also creates the database tables and the storage bucket.

### Without Docker

Start only the database, apply migrations, then run each app:

```bash
cp .env.example .env
make migrate
```

```bash
uv run --env-file .env uvicorn jalada.composition:build_api --factory --reload
```

```bash
uv run --env-file .env jalada-worker
```

```bash
cd apps/web && npm install && npm run dev
```

## Checks

```bash
make check
```

This runs ruff, mypy, the API and worker tests, ESLint, the TypeScript check and the web tests, the same as CI. `make test-integration` runs the database tests against Postgres in Docker. `make format` fixes formatting.

`make e2e` runs the main journey in a browser with Playwright: sign up, paste an M-Pesa message, wait for the worker to read it, confirm it, find it in the ledger, download the year's workbook and delete the account. It builds a separate copy of the whole stack under its own Docker project, so your local data is untouched, and removes it afterwards. Stop your own stack first (`make down`), because both use the same ports. Running it several times within a minute trips the sign-in rate limit. CI runs the same journey on every pull request.

After changing a table in `apps/api/src/jalada/adapters/database/tables.py`, generate a migration with `make migration name="what changed"`.

## Design

The web app is built for small Android phones first: large text, big tap targets and light pages. It uses the Onest font and a black, pumpkin, ivory and flax palette, with a dark theme that follows the phone's setting.

## Test data

All receipts, statements and certificates in this repo are made up. Never commit real financial documents or `.env` files.
