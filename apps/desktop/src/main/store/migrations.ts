import type { Database } from "better-sqlite3-multiple-ciphers";

/**
 * The local database's tables, one step per version. A step is never edited once shipped;
 * a change is a new step. The version lives in SQLite's own `user_version`.
 */
const STEPS: string[] = [
  // 1: entries copied from the server, and where sync got to.
  `CREATE TABLE entries (
     id TEXT PRIMARY KEY,
     kind TEXT NOT NULL,
     status TEXT NOT NULL,
     occurred_on TEXT,
     direction TEXT,
     amount_cents INTEGER,
     counterparty TEXT,
     category TEXT,
     category_name TEXT,
     purpose TEXT NOT NULL,
     mpesa_code TEXT,
     server_copy TEXT NOT NULL,
     pulled_at TEXT NOT NULL
   );
   CREATE INDEX entries_newest_first ON entries (occurred_on DESC, id);
   CREATE TABLE sync_state (name TEXT PRIMARY KEY, value TEXT NOT NULL);`,
];

export const LATEST = STEPS.length;

/** Brings the database up to the latest version, each step in its own transaction. */
export function migrate(db: Database): number {
  const current = db.pragma("user_version", { simple: true }) as number;
  for (let version = current; version < STEPS.length; version += 1) {
    db.transaction(() => {
      db.exec(STEPS[version] ?? "");
      db.pragma(`user_version = ${version + 1}`);
    })();
  }
  return LATEST;
}
