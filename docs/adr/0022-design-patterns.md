# 0022. Design patterns across the application

Status: Accepted
Date: 2026-11-07

## Context
Jalada AI will keep gaining providers, channels, rules and integrations. Each one should plug in without editing the code that uses it, and without inventing a new shape each time. This record names the patterns the codebase uses, where, and where they are still missing. It is a guide, not a reason to add abstraction where there is only ever one implementation.

## Decision

| Pattern | Use it for | In place | Still to do |
| --- | --- | --- | --- |
| Ports and adapters | Every vendor, database and file format | All modules (0020) | |
| Registry or factory | Choosing an implementation by name from settings | Language models (0021) | Evidence storage, OCR and text readers, chat channels (WhatsApp beside Telegram), email senders, issue trackers (Docket) |
| Chain of responsibility | Falling back across providers, or trying handlers in order until one answers | Language models (0021), on `core/resilience` | Text reading (pdfplumber, then Tesseract, then a model), classification (learned choice, then rules, then a model), detection |
| Strategy | Interchangeable rules chosen per call or per deployment | Model selection and retry policy (0021) | Tax rules per year, certificate matching, export formats (Excel, CSV) |
| Specification | Rules that can be listed, combined and tested one by one | | The verifier's checks, upload validation |
| Observer (domain events) | Reacting to something that happened without the code that did it knowing who listens | | Product events and telemetry, Telegram replies after processing, admin alerts |
| Outbox | Reliable sending to outside services | | Docket reports, eTIMS invoices, email |
| Unit of work and repository | One transaction per use case, data access behind an interface | All modules | One unit of work per module (0020) |
| Composition root | Wiring in one place | `composition.py`, `builders.py` | |

Rules of thumb:
- A pattern earns its place when there is, or will soon be, a second implementation, or when failure handling would otherwise be copied.
- The choice lives in settings or data; code that uses a port never branches on which implementation it got.
- Generic machinery goes in `core` (resilience, events), never knowing about a module.

## Consequences
- New work names its pattern in its decision record.
- The "Still to do" column is tracked in the roadmap as one item per row, done when the area is next changed rather than all at once.
