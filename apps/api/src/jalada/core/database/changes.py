"""Ordering changes by the transaction that made them, so readers can follow along.

Each changed row records the id of the database transaction that wrote it. A reader asks
which transactions are certainly finished, and reads only rows written by those. A row from
a transaction still running, even one that started earlier, is never skipped: it is read
on a later pass. Ordering by a plain counter or a clock would lose such rows.
"""

from sqlalchemy import TextClause, text
from sqlalchemy.orm import Session as DbSession

# The current transaction's id, as a plain number. Postgres 13 and later.
CURRENT_TRANSACTION: TextClause = text("(pg_current_xact_id()::text::bigint)")


def settled_before(db: DbSession) -> int:
    """Every transaction with a smaller id has finished, one way or the other."""
    return int(
        db.execute(
            text("SELECT pg_snapshot_xmin(pg_current_snapshot())::text::bigint")
        ).scalar_one()
    )
