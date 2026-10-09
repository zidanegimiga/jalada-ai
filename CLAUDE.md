# Ledger: purpose-aware money records for Kenyans

## What this is
A service that works out what each transaction was for (business or personal, earned income or support, a work cost or a household cost), then categorises and saves it with its evidence. It is a personal financial record first and a tax-ready record at filing time.

Users: Kenyans without accountants, with scattered income (salary, freelance work with withholding tax, informal businesses, support from relatives), many small spends, and often small or basic phones.

Planning doc (market scan, early architecture, decisions): https://claude.ai/code/artifact/d1e0238f-03c4-46b0-983d-f163aaab62d7

## How we work (read this first)
The owner, Zidane, is following a proper system design process and reviews every line. Do not run ahead.

1. **Design before code.** Work through `docs/design/` in order. Do not write application code for a stage until its design doc is marked `Status: Approved` by Zidane.
2. **One step at a time.** Propose a plan, wait for approval, then make the change. Never batch several stages into one change.
3. **Small diffs.** Keep each change reviewable in one sitting, roughly under 150 lines. Split anything bigger.
4. **Explain every change.** For each file touched, say what changed and why, in plain language. Point out trade-offs and anything you were unsure about.
5. **Decisions get an ADR.** Any choice of library, service, data store, or pattern gets an architecture decision record in `docs/adr/` before it lands in code. No new dependency without one.
6. **Tests with code.** Every code change comes with tests. Run them and show the result.
7. **Ask, don't assume.** If a requirement is unclear, ask. Do not invent tax rules or user needs.

## Writing style for explanations and docs
- Short sentences, flowing and easy to read. No em dashes.
- Avoid acronyms. If one is needed, spell it out the first time and say what it is.

## Product rules that never bend
- Never label a transaction as taxable or deductible on its own. Record what it was; tax views apply rules; unclear items stay marked for review.
- Raw evidence is permanent. Every record links to its original photo, message or file.
- The database is the source of truth. Google Sheets, Excel and tax summaries are generated views, never edited back in.
- Financial data is personal data under Kenya's Data Protection Act. Login per person, encryption, OWASP Top 10 web security checks, and a way to delete data, from the first version.

## Current state
- Stage: design, `docs/design/00-problem-and-users.md` is a draft awaiting review.
- `app/` holds early scaffolding (settings, database helper) written before the design process. Treat it as a spike: nothing in it is decided until an ADR confirms it.
- Stack under consideration (to be confirmed by ADRs): Python with FastAPI, PostgreSQL, Celery with RabbitMQ, S3-compatible storage, Claude for vision extraction, WhatsApp Cloud API, Africa's Talking for SMS and USSD.

## Domain notes
See `docs/domain/kenya-tax-notes.md` for what we learned filing a real 2025 return. Treat it as context to verify, not as tax advice.

## Never commit
Real financial records, receipts, statements, tax certificates, `.env` files or API keys. Test fixtures must be invented data.
