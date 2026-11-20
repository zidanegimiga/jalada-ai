import { rmSync } from "node:fs";
import { join } from "node:path";

import type { Database } from "better-sqlite3-multiple-ciphers";

import { openDatabase } from "./database";
import { EntryStore } from "./entries";
import { forgetKey, loadOrCreateKey, type KeyProtector } from "./key";
import { SyncState } from "./sync-state";

const ACCOUNT_ID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

/** One person's records on this computer, open while they are signed in. */
export type OpenStore = {
  entries: EntryStore;
  syncState: SyncState;
  close: () => void;
};

/**
 * Where each person's encrypted database and sealed key live, under the app's own data
 * folder: one database and one key per account, so people sharing a computer never share
 * records (decision 0029).
 */
export class LocalStore {
  constructor(
    private readonly folder: string,
    private readonly protector: KeyProtector,
  ) {}

  open(accountId: string): OpenStore {
    const { database, key } = this.files(accountId);
    const db: Database = openDatabase(
      database,
      loadOrCreateKey(key, this.protector),
    );
    return {
      entries: new EntryStore(db),
      syncState: new SyncState(db),
      close: () => db.close(),
    };
  }

  /** Signing out: the database, its write-ahead log and the key all go. */
  forget(accountId: string): void {
    const { database, key } = this.files(accountId);
    for (const file of [database, `${database}-wal`, `${database}-shm`]) {
      rmSync(file, { force: true });
    }
    forgetKey(key);
  }

  /** The account id comes from the server, but is checked anyway: it becomes a file name. */
  private files(accountId: string) {
    if (!ACCOUNT_ID.test(accountId)) throw new Error("Not an account id.");
    return {
      database: join(this.folder, "records", `${accountId}.db`),
      key: join(this.folder, "keys", `${accountId}.key`),
    };
  }
}
