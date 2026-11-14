# 0023. Transactions apart from evidence, with money accounts

Status: Accepted
Date: 2026-11-14
Design: [03. The money model](../design/03-money-model.md)

## Context
Every piece of evidence becomes one ledger entry. A payment message and the receipt for the same purchase are counted twice, moving money between your own accounts looks like spending, and money that is owed has nowhere to go. The tax workbook is only as good as the ledger behind it.

## Options
1. **Keep one entry per piece of evidence and add links between entries.** The smallest change, but every total then has to know which linked entries to skip, as certificate payments already do. That rule spreads into every query.
2. **Full double-entry bookkeeping.** Correct and well understood, but far more than users need, and every screen would have to hide it.
3. **Transactions apart from evidence, on money accounts, with single entry.** Money that moved is one record, documents link to it, and transfers move money between accounts instead of counting as income or spending.

## Decision
Option 3, as set out in design document 03:
- Money accounts, transactions with one or more lines, and links from transactions to evidence with a role.
- Obligations for invoices, settled by allocations.
- Matching apart from classification: exact matches only on a payment system code, everything else suggested to the user.
- An append-only audit trail.
- A transaction is not confirmed financial data until the user confirms it.

The model is built in the order the design gives, beside the current entries, which are retired once nothing reads them.

Money accounts live in the ledger module. Every user gets an M-Pesa and a Cash account when they sign up, and existing users get them in the migration that adds the table. The accounts module does not know about the ledger: sign-up takes a list of things to run when a user is created, in the same database transaction, and the composition root passes in the ledger's. This is the first use of the observer pattern from decision 0022, kept in process until there are domain events.

## Consequences
- Totals and the workbook read confirmed transaction lines, so there is one rule for what counts, not a skip list.
- For a while two models exist side by side. Each step keeps the tests passing, and a check compares totals before and after entries are copied across.
- Accounts not tracked by the user (a bank they never send statements for) still exist by name, so transfers to them are recorded correctly.
