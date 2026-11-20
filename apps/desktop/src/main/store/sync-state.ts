import type { Database } from "better-sqlite3-multiple-ciphers";

/** Where syncing got to, kept in the person's own database (the `sync_state` table). */
export class SyncState {
  constructor(private readonly db: Database) {}

  get(name: string): string | null {
    const row = this.db
      .prepare("SELECT value FROM sync_state WHERE name = ?")
      .get(name) as { value: string } | undefined;
    return row?.value ?? null;
  }

  set(name: string, value: string): void {
    this.db
      .prepare(
        `INSERT INTO sync_state (name, value) VALUES (?, ?)
         ON CONFLICT (name) DO UPDATE SET value = excluded.value`,
      )
      .run(name, value);
  }
}
