import { mkdirSync } from "node:fs";
import { dirname } from "node:path";

import Database from "better-sqlite3-multiple-ciphers";

import { migrate } from "./migrations";

export class WrongKey extends Error {
  constructor() {
    super("The local database could not be opened with its key.");
  }
}

/**
 * Opens one person's encrypted database (SQLCipher) and brings its tables up to date.
 * `key` is 64 hex characters, used as a raw key so no password stretching is needed.
 */
export function openDatabase(file: string, key: string): Database.Database {
  if (!/^[0-9a-f]{64}$/.test(key)) throw new WrongKey();
  mkdirSync(dirname(file), { recursive: true });
  const db = new Database(file);
  try {
    db.pragma("cipher='sqlcipher'");
    db.pragma(`key="x'${key}'"`);
    // Reading anything proves the key; a wrong one fails here, not halfway through.
    db.prepare("SELECT count(*) FROM sqlite_master").get();
  } catch {
    db.close();
    throw new WrongKey();
  }
  db.pragma("journal_mode = WAL");
  db.pragma("foreign_keys = ON");
  // Deleted rows are overwritten, not left readable in free pages.
  db.pragma("secure_delete = ON");
  migrate(db);
  return db;
}
