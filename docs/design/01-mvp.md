# 01. Minimum viable product

Status: Approved

## Scope

In the first version a user can:

1. Sign up and sign in with email and password, or with Google.
2. Capture evidence in the web app: upload a photo or PDF, or paste an M-Pesa message.
3. Capture evidence through a Telegram bot: send a photo or PDF, or forward an M-Pesa message.
4. Have each piece of evidence run through the pipeline, ending in a proposed ledger entry or the review queue.
5. Confirm or correct each proposed entry with one tap.
6. Browse the ledger with filters, and see a monthly view of money in and out, split between business and personal.
7. Download an Excel workbook for one tax year (1 January to 31 December) with five sheets: Instructions, Income, Expenses, Withholding Tax and Summary.
8. Export or delete all their data.

Not in this version: WhatsApp, SMS, USSD, Google Sheets sync, payments, bulk statement imports, and filing returns.

## Assumptions

These answer the open questions in `00-problem-and-users.md` for now.

- The first audience is Persona 1 (mixed income) and Persona 2 (informal business). Persona 3 is served by the same features but not designed for separately.
- English only at launch. All user-facing text lives in one place so Kiswahili can be added.
- Registered companies and people with an accountant are not the audience.
- One person, one ledger. A user with several businesses tags entries as business without naming which one.
- Amounts are in Kenyan shillings. A foreign amount is recorded with its shilling value from the M-Pesa or bank record that paid it.

## System overview

```
 phone browser ──► web (Next.js) ──► api (FastAPI) ──► Postgres
                                       │   ▲              ▲
 Telegram ──► webhook ─────────────────┘   │              │
                                       evidence        jobs table
                                       storage            │
                                     (MinIO / R2)         ▼
                                           ▲        worker (pipeline)
                                           └───────────┤
                                                       ├──► OCR port (Tesseract, pdfplumber)
                                                       └──► model port (Gemini, Ollama)
```

- The API stores the original file or text in evidence storage, writes an `evidence` row and a job in the same database transaction, and returns at once.
- The worker claims jobs from Postgres, runs the pipeline and writes the result.
- The web app polls the evidence status. Telegram users get a reply message when processing finishes.

## Data model

All tables have a `uuid` primary key and `created_at`. Every table with user data has a `user_id`, and every query filters by it through one repository base class, so no query can forget it. Money is stored as integer cents (`bigint`), never as floating point.

### Accounts

| Table | Key columns | Notes |
| --- | --- | --- |
| `users` | `email` (unique, case-insensitive), `password_hash` (nullable), `google_subject` (unique, nullable), `display_name` | A Google-only user has no password hash. |
| `sessions` | `token_hash` (unique), `user_id`, `expires_at`, `last_seen_at` | The cookie holds a random token. Only its hash is stored, so a database leak does not leak sessions. |
| `telegram_links` | `user_id`, `telegram_user_id` (unique) | One Telegram account per user. |
| `telegram_link_codes` | `code_hash`, `user_id`, `expires_at` | Eight-character codes without look-alike letters, valid for 10 minutes, used once. A new code replaces the last. |

### Evidence and processing

| Table | Key columns | Notes |
| --- | --- | --- |
| `evidence` | `source` (web_upload, web_paste, telegram), `kind` (unknown, mpesa_message, statement, receipt, withholding_certificate, payslip, free_text), `storage_key`, `content_type`, `size_bytes`, `sha256`, `status` (received, processing, proposed, needs_review, confirmed, failed) | Unique on (`user_id`, `sha256`) so the same file is not processed twice. Pasted text is stored as a text object too, so all evidence lives in one place. |
| `jobs` | `kind`, `payload` (jsonb), `status` (queued, running, done, failed), `attempts`, `run_after`, `locked_until`, `last_error` | Claimed with `SELECT ... FOR UPDATE SKIP LOCKED`. A job whose lock expires is retried. |
| `pipeline_runs` | `evidence_id`, `outcome` (proposed, needs_review, duplicate, failed), `attempts`, `input_tokens`, `output_tokens`, `cost_usd`, `started_at`, `finished_at` | One per processing attempt of a piece of evidence. |
| `pipeline_steps` | `run_id`, `step` (detect, extract, classify, verify), `attempt`, `input`, `output` (jsonb), `verdict`, `duration_ms` | The trace that explains how an entry was decided. Inputs describe what a step was given (kind, text length), never the raw evidence text, which stays encrypted in storage. Never written to logs. |

### Ledger

| Table | Key columns | Notes |
| --- | --- | --- |
| `entries` | `evidence_id`, `run_id`, `kind` (transaction, withholding_certificate), `status` (proposed, confirmed, rejected), `occurred_on`, `direction` (in, out), `amount_cents`, `counterparty`, `reference`, `mpesa_code`, `certificate_serial`, `tax_withheld_cents`, `purpose` (business, personal, unsure), `category_id`, `confidence`, `confirmed_at` | Unique on (`user_id`, `mpesa_code`) and on (`user_id`, `certificate_serial`) where not null. These are the duplicate guards. |
| `entry_revisions` | `entry_id`, `before`, `after` (jsonb), `changed_at` | Every correction is kept, so the history of an entry is visible. |
| (categories) | `slug`, `name`, `direction`, `purpose` | A fixed list in code, `domain/categories.py`. Entries store the slug. It moves to a table only if users get their own categories. |
| `counterparty_preferences` | `user_id`, `counterparty_key`, `category_id`, `purpose`, `times_used` | Written when a user confirms or corrects an entry. The classifier checks this first. |
| `certificate_payments` | `payment_id` (key), `certificate_id`, `user_id`, `linked_at` | A payment linked to the withholding certificate it settled. The payment is then counted through the certificate. |

### Category list

Income and costs follow the kinds in `docs/domain/kenya-tax-notes.md`.

- **Money in:** salary, consultancy or freelance fees, business sales, support from family or friends, transfer between own accounts, refund, other.
- **Business costs:** data and airtime, transport, equipment that lasts years, software and subscriptions, workspace rent, stock and supplies, professional fees, other.
- **Personal costs:** food, rent, transport, airtime and data, family support given, school fees, health, other.

## Pipeline

One run takes one piece of evidence for one user. Each step is its own function with typed input and output.

1. **Detect.** Decide the evidence kind. Rules first: M-Pesa messages and certificates have recognisable text. PDFs go through pdfplumber, images through OCR. The model is asked only if the rules return `unknown`.
2. **Extract.** Fill a strict Pydantic schema: date, amount, direction, counterparty, reference, M-Pesa code, certificate serial, tax amounts. M-Pesa messages and certificates use parsers. Receipts and free text use OCR text plus the model with the schema as structured output.
3. **Classify.** Propose purpose and category. Order: the user's own `counterparty_preferences`, then shared rules (for example, a known payroll counterparty is salary), then the model.
4. **Verify.** Reject the result if the schema is invalid, amounts do not add up (for example gross minus withheld tax), the date is in the future or more than seven years old, the M-Pesa code or certificate serial already exists for this user, or confidence is below the threshold.

**Budget**, from settings: at most 3 attempts, 8,000 tokens and US$0.02 per run.

**Stop conditions:** the verifier passes, the budget runs out, or the verifier fails twice.

**Outcome:** a pass becomes a `proposed` entry. Everything else becomes `needs_review`, with whatever was extracted filled in. A duplicate is marked `duplicate` and links to the existing entry. Nothing is ever marked taxable or deductible by the pipeline.

**Report:** each step writes a `pipeline_steps` row, and the run writes its totals. Every model call is traced with OpenTelemetry and sent to Langfuse.

**Learning:** confirming or correcting an entry upserts `counterparty_preferences`, so the next payment to the same counterparty is classified from the user's own choice.

**Ports:** `LanguageModel` (answer in JSON matching a schema, from text or a photo), `TextReader` (pasted text, PDFs, and photos through OCR), `EvidenceStore` (put, get, delete), `JobQueue` (enqueue, claim, complete, fail), `Clock`. Fakes of each are used in tests and evaluations.

### Evaluation suite

`evals/fixtures/` holds at least 20 invented pieces of evidence (M-Pesa messages, receipts, certificates and payslips) each with an expected result. A script runs the pipeline on them with the real parsers and a recorded or fake model, and reports extraction accuracy, classification accuracy and how often the verifier correctly rejects broken output. CI fails below agreed thresholds, starting at 90%, 80% and 95%.

## API

All routes are under `/v1`, take and return JSON unless noted, and need a session cookie except sign-up, sign-in, the Google callback, the Telegram webhook and `/health`. Errors return `{"error": {"code": "...", "message": "..."}}`.

| Method and path | Purpose |
| --- | --- |
| `POST /v1/auth/signup` | Email and password sign-up. Sets the session cookie. |
| `POST /v1/auth/login` | Email and password sign-in. |
| `POST /v1/auth/logout` | Ends the session. |
| `GET /v1/auth/google/start`, `GET /v1/auth/google/callback` | Google sign-in. |
| `GET /v1/me` | The signed-in user. |
| `POST /v1/evidence` | Multipart upload of a photo or PDF. Returns the evidence id and status. |
| `POST /v1/evidence/text` | A pasted M-Pesa message or free text. |
| `GET /v1/evidence/{id}` | Status and, once processed, the entry it produced. |
| `GET /v1/evidence` | The user's evidence, newest first. |
| `GET /v1/evidence/{id}/file` | The original, decrypted, after an ownership check. Signed links come with Telegram replies. |
| `GET /v1/review` | Entries that are proposed or need review, oldest first. |
| `POST /v1/entries/{id}/confirm` | Confirms a proposed entry as it is. |
| `PATCH /v1/entries/{id}` | Corrects fields and confirms. |
| `GET /v1/entries` | The ledger, filtered by date range, direction, purpose, category and status, with cursor paging. |
| `GET /v1/summary/monthly?year=` | Money in and out per month, split by business and personal. |
| `GET /v1/categories` | The category list. |
| `GET /v1/exports/{year}.xlsx` | The tax year workbook. |
| `GET /v1/certificates/{id}` | A withholding certificate, the payments linked to it, and up to five likely payments to link. |
| `POST /v1/certificates/{id}/payments`, `DELETE /v1/certificates/{id}/payments/{payment_id}` | Link or unlink a payment. |
| `POST /v1/telegram/link-code` | Creates a code to link a Telegram account. |
| `POST /v1/telegram/webhook` | Telegram updates. Checked against the secret token header. |
| `GET /v1/account/export` | A zip of everything held about the user: account, entries and revisions, evidence details with every original file, pipeline runs and remembered choices. No password hash or session data. |
| `DELETE /v1/account` | Takes the account's email typed again. Deletes every evidence file, then the user, which cascades to all their rows, and their queued jobs. Signs them out. |

**Limits:** sign-in and sign-up allow 5 attempts per minute per address and per IP address. Uploads allow 60 per hour per user, up to 10 MB each, of type JPEG, PNG, WebP or PDF, checked by reading the file's first bytes, not by trusting its name or declared type.

## User flows

**First visit.** Land on a short page, sign up with Google or email, accept the privacy notice (what is stored, where, and that Telegram keeps its own copy of anything sent there), land on an empty home screen with one action: add evidence.

**Web capture.** Tap add evidence, choose camera, file or paste. The item appears at the top of the list as processing, then turns into a proposed entry or a "needs a look" card.

**Telegram capture.** On the home screen, tap Link Telegram to get a code and a link that opens the bot with the code filled in. From then on, any photo, PDF or forwarded message sent to the bot becomes evidence. The bot replies with the proposed entry and a link to review it.

**Review.** A list of cards, newest last. Each shows the amount, counterparty, date, proposed purpose and category, and a thumbnail of the evidence. Confirm is one tap. Edit opens a short form with large controls.

**Ledger and month view.** The home screen shows this month's money in and out, split into business and personal, in the style of the balance card in the design. Below it is the entry list with filters for month, direction, purpose and category.

**Export.** Choose a year and download the workbook.

**Download and delete.** On the account screen, Download my data gives one zip with everything, originals included. Delete my account asks for the email typed out, then removes everything and signs out.

## Excel export

| Sheet | Contents |
| --- | --- |
| Instructions | What each sheet is, the year covered, that figures are records and not tax advice, and which iTax sheet each section relates to. |
| Income | Confirmed money in, grouped as employment (relates to `F_Employment_Income`), business and consultancy (relates to `B_Profit_Loss_Account_Self`), and not income (support, own transfers, refunds), each with date, counterparty, amount and evidence link. |
| Expenses | Confirmed business costs, with items that last years flagged separately for capital allowance, and a column for whether an eTIMS invoice is attached. Personal costs are left out. |
| Withholding Tax | One row per certificate: payer, payer tax number, serial number, date, gross amount, tax withheld, the payments linked to it (relates to `O_WHT_Credits`). |
| Summary | Totals per group and per month. No tax is calculated. |

Text taken from evidence is always written as plain text, so a counterparty such as `=HYPERLINK(...)` can never become a live formula. Every sheet prints landscape, one page wide.

## Security and privacy

- Passwords hashed with Argon2. Sessions in secure, HTTP-only, same-site cookies.
- Evidence encrypted by the application before upload, with a key from settings, and served only to its owner through the API.
- Logs carry a request id and never raw financial text, amounts or file contents.
- Free model tiers and local models only see invented data. Real users' evidence goes only to a provider whose terms exclude training on it (decision 0012).
- Export and delete are in the first version.

## Certificates and the payments that settled them

A withholding certificate and the M-Pesa or bank deposit for the same job describe the same income. The user links them from the certificate in the ledger. Jalada suggests up to five confirmed deposits from 90 days before to 60 days after the certificate's date: the exact expected amount (gross minus tax withheld) first, then the same payer, then the nearest date. A certificate can have several payments; a payment settles one certificate; linked payments cannot add up to more than the gross amount.

A linked payment is counted through its certificate: the workbook's income sections and the monthly view leave it out, and the Withholding Tax sheet shows it. Links are stored in `certificate_payments` (`payment_id` as the key, `certificate_id`, `user_id`, `linked_at`). Nothing is linked automatically.
