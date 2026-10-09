# Design process

We design in stages. Each stage is one document. A stage moves to the next only after Zidane reviews it and changes its status to `Approved`.

| # | Stage | Question it answers | Status |
|---|---|---|---|
| 00 | [Problem and users](00-problem-and-users.md) | Who is this for, and what do they need to get done? | Draft |
| 01 | [Requirements](01-requirements.md) | What must the system do, and how well? | Not started |
| 02 | [Domain model](02-domain-model.md) | What are the things we track, and what categories exist? | Not started |
| 03 | [Key user flows](03-user-flows.md) | What does each journey look like step by step? | Not started |
| 04 | [Estimates](04-estimates.md) | How much data, traffic and model cost per user? | Not started |
| 05 | [High-level architecture](05-architecture.md) | What are the parts and how do they talk? | Not started |
| 06 | [Interfaces](06-interfaces.md) | What are the API endpoints, events and message formats? | Not started |
| 07 | [Data model](07-data-model.md) | What tables, keys and constraints? | Not started |
| 08 | [Deep dives](08-deep-dives.md) | Extraction, classification, duplicates, security and privacy | Not started |
| 09 | [Build plan](09-build-plan.md) | What do we build first, in what slices? | Not started |

Decisions made along the way are recorded as architecture decision records in [`../adr/`](../adr/).

## How each stage runs
1. Claude drafts or asks questions, depending on how much is already known.
2. Zidane reviews, comments and edits.
3. Open questions are answered or written down as assumptions.
4. Zidane sets `Status: Approved`. Only then does the next stage start.
