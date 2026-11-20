import type { Database } from "better-sqlite3-multiple-ciphers";

import type { LocalEntry } from "@shared/records";

/** An entry as the API sends it, with the fields the desktop app reads. */
export type ServerEntry = {
  id: string;
  kind: string;
  status: string;
  occurred_on: string | null;
  direction: string | null;
  amount_cents: number | null;
  counterparty: string | null;
  category: string | null;
  category_name: string | null;
  purpose: string;
  mpesa_code: string | null;
  /** Missing from a server older than entry versions. */
  version?: number;
};

const COLUMNS =
  "id, kind, status, occurred_on, direction, amount_cents, counterparty, category, category_name, purpose, mpesa_code, version";

/** The entries copied from the server, read and written in this computer's database. */
export class EntryStore {
  constructor(private readonly db: Database) {}

  /** Keeps the server's copies, replacing older ones, all or nothing. */
  saveFromServer(entries: ServerEntry[], pulledAt: string): void {
    const save = this.db.prepare(
      `INSERT INTO entries (${COLUMNS}, server_copy, pulled_at)
       VALUES (@id, @kind, @status, @occurred_on, @direction, @amount_cents, @counterparty,
               @category, @category_name, @purpose, @mpesa_code, @version, @server_copy,
               @pulled_at)
       ON CONFLICT (id) DO UPDATE SET
         kind = excluded.kind, status = excluded.status, occurred_on = excluded.occurred_on,
         direction = excluded.direction, amount_cents = excluded.amount_cents,
         counterparty = excluded.counterparty, category = excluded.category,
         category_name = excluded.category_name, purpose = excluded.purpose,
         mpesa_code = excluded.mpesa_code, version = excluded.version,
         server_copy = excluded.server_copy,
         pulled_at = excluded.pulled_at`,
    );
    this.db.transaction(() => {
      for (const entry of entries) {
        save.run({
          ...entry,
          version: entry.version ?? 0,
          server_copy: JSON.stringify(entry),
          pulled_at: pulledAt,
        });
      }
    })();
  }

  /**
   * One page of the change feed: entries to keep, entries no longer in the ledger, and where
   * the feed got to, all saved together or not at all.
   */
  applyChanges(
    kept: ServerEntry[],
    gone: string[],
    pulledAt: string,
    position: { name: string; value: string },
  ): void {
    const remove = this.db.prepare("DELETE FROM entries WHERE id = ?");
    const mark = this.db.prepare(
      `INSERT INTO sync_state (name, value) VALUES (?, ?)
       ON CONFLICT (name) DO UPDATE SET value = excluded.value`,
    );
    this.db.transaction(() => {
      this.saveFromServer(kept, pulledAt);
      for (const id of gone) remove.run(id);
      mark.run(position.name, position.value);
    })();
  }

  /** Newest first, a page at a time. */
  list(limit = 50, offset = 0): LocalEntry[] {
    return this.db
      .prepare(
        `SELECT ${COLUMNS} FROM entries
         ORDER BY occurred_on DESC, id LIMIT ? OFFSET ?`,
      )
      .all(limit, offset)
      .map(toLocalEntry);
  }

  count(): number {
    return (
      this.db.prepare("SELECT count(*) AS n FROM entries").get() as {
        n: number;
      }
    ).n;
  }
}

function toLocalEntry(row: unknown): LocalEntry {
  const r = row as ServerEntry;
  return {
    id: r.id,
    status: r.status,
    occurredOn: r.occurred_on,
    direction:
      r.direction === "in" || r.direction === "out" ? r.direction : null,
    amountCents: r.amount_cents,
    counterparty: r.counterparty,
    categoryName: r.category_name,
    purpose: r.purpose,
  };
}
