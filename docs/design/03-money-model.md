# 03. The money model

Status: Approved

[02. The user journey today](02-user-journey-today.md) ends with the problem this document solves: every piece of evidence becomes a transaction of its own. A payment message and the receipt for the same purchase are counted twice, a payment message cannot say what the money was for, moving money between your own accounts looks like spending, and money that is owed has no place at all.

This document sets the model that replaces it, the user journeys built on it, and the order it is built in. How chat and the assistant work is in a separate document (04).

## Principles
1. **Evidence is not a transaction.** Evidence tells us about money. A transaction is money that actually moved. One transaction can have many pieces of evidence, and one piece of evidence (a statement) can describe many transactions.
2. **AI proposes, domain rules decide, the user resolves.** Models read documents and suggest categories. They never create a confirmed record, and they never decide that two documents describe the same payment.
3. **Every number can be explained.** Each amount in the ledger and the tax workbook traces back to its transaction, its evidence, the original file, how it was read and classified, any matches, and who confirmed or changed it.

And one rule with no exceptions:

> **A transaction may be proposed automatically, but it is not confirmed financial data until the user confirms it.**

This holds even when the amount comes from an M-Pesa message read with rules and the counterparty was classified by the user before. Jalada does all the work up to that point, so confirming should cost one tap.

## Concepts

| Concept | What it is | Examples |
| --- | --- | --- |
| **Money account** | Somewhere money sits | M-Pesa, KCB, Equity, cash, a card, Fuliza |
| **Transaction** | Money that moved in or out of one of the user's accounts, or between two of them | Paid Naivas KSh 2,350 from M-Pesa |
| **Transaction line** | What part of a transaction was for: category, business or personal, amount | KSh 2,000 groceries (personal), KSh 350 printer paper (business) |
| **Evidence** | Anything the user sends, kept unchanged | A forwarded message, a receipt photo, a PDF invoice, a statement |
| **Document role** | What a piece of evidence does for a transaction | Payment proof, receipt, invoice, certificate, payslip, statement |
| **Obligation** | Money expected but not yet moved | An invoice the user issued (owed to them), a bill they received (they owe) |
| **Allocation** | How much of a transaction settles an obligation | KSh 45,000 of a deposit settles invoice INV-012 |
| **Match** | A link between evidence and a transaction, or a transaction and an obligation, and how it was made | Exact code, suggested and confirmed by the user, made by hand |
| **Audit event** | One thing that happened to the records, never changed afterwards | Created, classified, matched, unmatched, confirmed, changed from A to B |

Users see three of these:
- **Money:** money in, money out and transfers.
- **Documents:** receipts, invoices, certificates and statements, and what each one explains.
- **To check:** what Jalada needs the user to decide.

## Transactions

A transaction has an account, a date, an amount, a direction (in, out or transfer), a counterparty, a reference such as an M-Pesa code, a status, and one or more lines.

**Lines exist from the start.** Every transaction has at least one line holding the category, business or personal, and the amount. The screens show one line until the user splits a transaction. Receipt line items fit into the same shape later, so splitting is not a special case and needs no second migration.

**Transfers.** Money moving between two of the user's own accounts is one transaction of kind transfer, with a from-account and a to-account. It is never income or spending. Internally it moves money out of one account and into the other, and the user sees one transfer. When the other account is not tracked, such as a bank the user never sends statements for, the transfer still goes to that account by name. The user marks a paybill or bank as theirs once, and Jalada remembers it.

**Reversals and refunds.** A reversal cancels the transaction it reverses, so the two count as zero. A refund is money back for an earlier payment and is linked to it, so it reduces that spending instead of counting as income. Both are suggested and confirmed like any match. The exact wording of reversal messages goes in `docs/domain/mpesa-messages.md`, checked against real invented examples, before any rule reads them.

**Fuliza and loans** are a later step. Money borrowed is not income and repaying it is not spending. Until it is built, these stay in To check with a note.

## Evidence and what it creates

| Evidence | When nothing matches | When it matches |
| --- | --- | --- |
| M-Pesa or bank message | A proposed transaction on that account | Becomes payment proof for the existing transaction or candidate |
| Receipt | A **candidate**: a purchase that probably happened, with no payment yet | Becomes the receipt for the payment, and supplies the category and later the line items |
| Invoice the user issued | An obligation owed to the user | A deposit settles it |
| Invoice or bill the user received | An obligation the user owes | A payment settles it |
| Withholding certificate | Income earned with tax withheld, as today | Deposits settle it, as `certificate_payments` does today |
| Payslip | A proposed income transaction with its deductions as lines | Supports the salary deposit |
| Statement | Many proposed transactions | Each line matches an existing transaction by its code, so nothing is counted twice |
| Not about money | Nothing, once the user marks it "Not a transaction" | |

**Candidates.** A receipt that arrives first does not become a transaction, because Jalada does not know if or how it was paid. It waits as a candidate. When the payment message arrives, the match is suggested. If nothing arrives within a few days, To check asks: "Paid in cash, by card, or still to pay?" Cash or card turns the candidate into a transaction on that account. A candidate never counts in any total.

## Matching

Matching answers one question: do these describe the same money? It is separate from classification, which answers what the money was for. A category, or the fact that two items share one, is never evidence that they are the same payment.

There are two kinds of match:

**Exact.** Made without asking when two items share an identifier issued by the payment system:
- the same M-Pesa code, or the same bank transaction ID or statement reference;
- read from text (a message or a statement), not from a photo;
- and the amounts are equal.

A code read from a photo can be misread, so it only counts as exact when it has the right format and the amount is equal too. Otherwise it is a suggestion.

An exact match only links evidence to a transaction. It does not confirm the transaction.

**Suggested.** Everything else is offered to the user and never applied without them:
- the same amount, a date within a few days, and a similar counterparty name or till number;
- a deposit that fits an open invoice;
- a refund that fits an earlier payment.

When several items fit, all of them are offered. Wrongly merging two payments is worse than asking one question, so the threshold for suggesting is low and the threshold for linking without asking is an exact identifier.

Every match records how it was made (exact, suggested and accepted, or by hand) and can be undone. Undoing a match is an audit event, not a deletion.

## Lifecycle

Inside the system:

```
evidence received → read → candidate or proposed transaction → matched → ready → confirmed
```

What the user sees:

| State | Shown as |
| --- | --- |
| Being read | "Reading your receipt" |
| Ready, no open questions | "Ready to confirm" |
| Open questions: no category, a suggested match, uncertain fields | "Needs a look", with the question |
| Confirmed | "In your records" |
| Linked to other evidence | "Receipt linked to your M-Pesa payment" |
| Not about money | "Not a transaction" |

## Confirming cheaply
- **One tap** for a transaction with no open questions: the amount, who, when, the category, business or personal, and its evidence, with Confirm and Change.
- **Confirm all** for the items marked "Ready to confirm". It never includes an item with a suggested match, a missing category or a field the verifier doubted. The list shows what will be confirmed before the tap.
- **Questions instead of forms** when something is unclear: "Is this the same purchase?", "Paid in cash or by card?", "Business or personal?"
- Jalada should get quieter over time: learned categories mean more items arrive ready, but every one is still confirmed by the user.

## What counts where

| Record | Monthly view and tax workbook |
| --- | --- |
| Evidence on its own | Never |
| Candidate | Never |
| Proposed transaction (not confirmed) | Never. The workbook checks list it. |
| Confirmed transaction | Yes, by its lines |
| Transfer | Never as income or spending. Shown under transfers. |
| Reversal and the transaction it reverses | Together count as zero |
| Refund | Reduces the spending it refunds |
| Obligation | Never as income or spending. Shown as owed. |
| Payment that settles an obligation or a certificate | Counted once, through what it settles where the tax rules need that |

**Data quality before download.** The tax workbook keeps working with incomplete records, but it says so first, for example: 12 items to check, 7 receipts with no payment, 4 unpaid invoices, 2 certificates with no deposit, 1 file that could not be read, 3 possible duplicates. The same summary goes on a Checks sheet in the workbook.

## User journeys

The web and every chat channel use the same use cases. Chat is for sending and quick answers. The web is for reviewing, bulk work and reports.

**First visit.** A short explanation before anything else: send receipts, M-Pesa messages, statements and invoices, and Jalada organises them into records you check and use at tax time. One action: add your first document.

**Paid by M-Pesa, then sends the receipt.**
1. The message arrives: a proposed KSh 2,350 payment to Naivas from M-Pesa, which needs a category.
2. The receipt arrives: a candidate with the same amount and date and a similar name. To check shows "We found a receipt that may belong to this payment", with Yes, same purchase and Not the same.
3. Yes links them. The receipt supplies the category, and the transaction is ready to confirm.

**Receipt first, message later.** The receipt waits as a candidate. The message arrives and the same suggestion appears. If no message ever comes, To check asks how it was paid.

**Moved M-Pesa to the bank.** The first time, Jalada asks if the paybill is the user's own account. After that it is proposed as a transfer.

**Got paid for an invoice.** The user records an invoice (a photo, a PDF, or typed in). A deposit from the same client arrives, and To check asks if it settles the invoice. A certificate explains any tax withheld.

**Sends a statement.** "38 new, 112 already recorded, 12 need a look."

**Reviewing on the web.**
- To check: questions first, then the ready items with Confirm all.
- Money: the ledger. Each row opens a page with the evidence, the lines, the matches and the history.
- Documents: everything sent and what each one explains, with receipts that have no payment and invoices that are unpaid.

**Tax time.** Pick a year, see the data quality summary, then download.

**In chat.** The same journeys as short messages with buttons: "KSh 2,350 to Naivas on 7 Nov. What was it for?" Corrections in plain words ("that was fuel for the business") and questions ("how much did I spend on transport in October?") come with the assistant in document 04.

## Data model

New tables, with the same rules as today: a `user_id` on every row, every query scoped by it, amounts in integer cents.

| Table | Key columns | Notes |
| --- | --- | --- |
| `money_accounts` | `kind` (mpesa, bank, cash, card, loan), `name`, `tracked`, `identifiers` (jsonb: paybill, account number ending) | Every user starts with M-Pesa and Cash. |
| `transactions` | `account_id`, `kind` (payment, transfer, reversal, refund), `direction`, `to_account_id`, `occurred_on`, `amount_cents`, `counterparty`, `reference`, `status` (candidate, proposed, confirmed, rejected), `run_id`, `confirmed_at` | Unique on (`user_id`, `reference`) for payment system codes, which is the duplicate guard. |
| `transaction_lines` | `transaction_id`, `amount_cents`, `category`, `purpose` | Lines add up to the transaction amount. |
| `transaction_evidence` | `transaction_id`, `evidence_id`, `role`, `matched_by` (exact, suggested, user), `matched_at` | Many to many. |
| `related_transactions` | `transaction_id`, `related_id`, `kind` (reverses, refunds) | |
| `match_suggestions` | `kind`, the two sides, `score`, `reasons`, `status` (open, accepted, declined) | Declined suggestions are kept so they are not offered again. |
| `obligations` | `kind` (receivable, payable), `counterparty`, `number`, `issued_on`, `due_on`, `amount_cents`, `status` (open, part paid, paid, cancelled) | |
| `allocations` | `obligation_id`, `transaction_id`, `amount_cents` | Allocations never add up to more than the obligation. |
| `audit_events` | `subject_type`, `subject_id`, `actor` (user, pipeline, system), `action`, `before`, `after`, `at` | Append only. Replaces `entry_revisions` once entries are gone. |

`evidence` keeps its table, gains the `not_a_transaction` status (done), and loses the assumption that it has at most one entry.

## Moving from entries

Done in small steps, each one shipped with its tests passing:
1. Add `money_accounts`, and give every user M-Pesa and Cash.
2. Add `transactions`, `transaction_lines` and `transaction_evidence` beside `entries`.
3. A migration copies every entry into a transaction with one line and one evidence link, and certificates keep their links. A check compares the totals before and after.
4. The pipeline writes transactions, and To check, the ledger, the month view and the workbook read them, one screen per step.
5. `audit_events` replaces `entry_revisions`, with the old revisions copied in.
6. `entries` is dropped once nothing reads it.

## Build order
1. Not a transaction (done).
2. This document, then a decision record for the model.
3. Money accounts.
4. Transactions, lines and evidence links, and moving from entries.
5. Audit events.
6. Exact matching on payment codes.
7. Receipt candidates and suggested matches, with the new To check card.
8. Confirm all.
9. Transfers, then reversals and refunds.
10. Statements as containers, with reconciliation.
11. Obligations: invoices issued and received.
12. Line items and splitting.
13. The data quality summary and Checks sheet in the workbook.
14. The ledger detail page and the Documents view.
15. The first-visit explanation on Home.

The assistant and chat journeys (document 04) build on steps 4 to 8.

## Not in this version
- Full double-entry bookkeeping. Accounts and transfers cover what users need without it.
- Generating invoices for users to send. Recording them only.
- Separate business and personal books. Purpose stays on each line.
- Anything confirmed without the user.

## Open questions
1. How many days a receipt waits for its payment before Jalada asks how it was paid. Starting point: 3 days.
2. Whether business expenses need an eTIMS invoice to be deductible, and what Jalada should then read from receipts. To be checked with the Kenya Revenue Authority and written up in `docs/domain/` before it changes any rule.
3. The wording of reversal, refund and Fuliza messages, from invented examples, in `docs/domain/mpesa-messages.md`.
