import type { Account, LedgerStatus } from "@shared/bridge";
import type { LocalChange, LocalEntry } from "@shared/records";

import type { LocalStore, OpenStore } from "../store/local-store";
import { CHANGE_KINDS } from "./change-kinds";
import { LAST_PULLED, pullLedger } from "./pull-ledger";
import { sendChanges } from "./send-changes";

type LedgerSyncPorts = {
  apiOrigin: string;
  store: LocalStore;
  fetch: (url: string, init: RequestInit) => Promise<Response>;
  /** The signed-in session's token, or null. */
  token: () => string | null;
  /** The server no longer accepts the session: sign out on this computer. */
  sessionEnded: () => void;
  /** The ledger on this computer changed, or a pull started or stopped. */
  changed: (status: LedgerStatus) => void;
  /** A change made here was added or moved to another state. */
  changesChanged: () => void;
  /** Ids for new changes, which are also their Idempotency-Keys. */
  newId: () => string;
  /** Records could not be kept on this computer, with why. */
  failed: (message: string) => void;
  now?: () => Date;
};

/** Sent changes stay in the list a week, so people can see what went. */
const KEEP_SENT_MS = 7 * 24 * 60 * 60 * 1000;

/**
 * Keeps the signed-in person's ledger on this computer and up to date (decision 0029). The
 * window always reads from here, online or not. Each sync sends the changes made here
 * first, in order, then refreshes the copy, so it includes what was just sent.
 */
export class LedgerSync {
  private open: OpenStore | null = null;
  private pulling: Promise<void> | null = null;
  /** A change was added while a sync ran, perhaps after it sent: run once more after it. */
  private again = false;

  constructor(private readonly ports: LedgerSyncPorts) {}

  /** Opens the person's records after sign-in, or closes them after sign-out. */
  switchTo(account: Account | null): void {
    this.open?.close();
    this.open = null;
    if (account) {
      try {
        this.open = this.ports.store.open(account.id);
      } catch (error) {
        // No secure keychain, say: signed in, but nothing is kept on this computer.
        this.ports.failed((error as Error).message);
      }
    }
    this.ports.changed(this.status());
    this.ports.changesChanged();
    if (this.open) void this.pull();
  }

  /** Sends changes and refreshes from the server, once at a time; nothing when signed out. */
  pull(): Promise<void> {
    if (this.pulling) return this.pulling;
    this.pulling = this.run().finally(() => {
      this.pulling = null;
      this.ports.changed(this.status());
      if (this.again) {
        this.again = false;
        void this.pull();
      }
    });
    this.ports.changed(this.status());
    return this.pulling;
  }

  /**
   * Keeps a change on this computer straight away, then tries to send it. Returns false
   * when the input is not acceptable or nobody's records are open.
   */
  addChange(kind: string, input: unknown): boolean {
    const known = CHANGE_KINDS[kind];
    const payload = known?.accept(input);
    if (!this.open || !known || payload === null || payload === undefined)
      return false;
    this.open.changes.add({
      id: this.ports.newId(),
      kind,
      payload,
      summary: known.summary(payload),
      createdAt: this.now().toISOString(),
    });
    this.changeMade();
    return true;
  }

  private changeMade(): void {
    this.ports.changesChanged();
    if (this.pulling) this.again = true;
    else void this.pull();
  }

  /** Sends a change that needs attention again, after the person has looked at it. */
  tryAgain(id: string): boolean {
    const done = this.open?.changes.tryAgain(id) ?? false;
    if (done) this.changeMade();
    return done;
  }

  discard(id: string): boolean {
    const done = this.open?.changes.discard(id) ?? false;
    if (done) this.ports.changesChanged();
    return done;
  }

  changes(): LocalChange[] {
    return this.open?.changes.list() ?? [];
  }

  /** Changes the server does not have yet. */
  unsent(): number {
    return this.open?.changes.unsent() ?? 0;
  }

  list(limit: number, offset: number): LocalEntry[] {
    return this.open?.entries.list(limit, offset) ?? [];
  }

  status(): LedgerStatus {
    return {
      entries: this.open?.entries.count() ?? 0,
      updatedAt: this.open?.syncState.get(LAST_PULLED) ?? null,
      updating: this.pulling !== null,
    };
  }

  private async run(): Promise<void> {
    const store = this.open;
    const token = this.ports.token();
    if (!store || !token) return;
    const connection = {
      apiOrigin: this.ports.apiOrigin,
      token,
      store,
      fetch: this.ports.fetch,
      now: () => this.now(),
    };
    try {
      const sent = await sendChanges({
        ...connection,
        changed: this.ports.changesChanged,
      });
      if (sent.outcome === "signed-out") return this.ports.sessionEnded();
      store.changes.clearSentBefore(
        new Date(this.now().getTime() - KEEP_SENT_MS).toISOString(),
      );
      const result = await pullLedger(connection);
      if (result.outcome === "signed-out") this.ports.sessionEnded();
    } catch {
      // Signed out while pulling, so the database closed under it: nothing more to do.
    }
  }

  private now(): Date {
    return this.ports.now?.() ?? new Date();
  }
}
