import type { Account, LedgerStatus } from "@shared/bridge";
import type { LocalEntry } from "@shared/records";

import type { LocalStore, OpenStore } from "../store/local-store";
import { LAST_PULLED, pullLedger } from "./pull-ledger";

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
  /** Records could not be kept on this computer, with why. */
  failed: (message: string) => void;
  now?: () => Date;
};

/**
 * Keeps the signed-in person's ledger on this computer and up to date (decision 0029). The
 * window always reads from here, online or not; pulls only refresh it.
 */
export class LedgerSync {
  private open: OpenStore | null = null;
  private pulling: Promise<void> | null = null;

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
    if (this.open) void this.pull();
  }

  /** Refreshes from the server, once at a time; does nothing when signed out. */
  pull(): Promise<void> {
    if (!this.pulling) {
      this.pulling = this.run().finally(() => {
        this.pulling = null;
        this.ports.changed(this.status());
      });
      this.ports.changed(this.status());
    }
    return this.pulling;
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
    try {
      const result = await pullLedger({
        apiOrigin: this.ports.apiOrigin,
        token,
        store,
        fetch: this.ports.fetch,
        now: this.ports.now ?? (() => new Date()),
      });
      if (result.outcome === "signed-out") this.ports.sessionEnded();
    } catch {
      // Signed out while pulling, so the database closed under it: nothing more to do.
    }
  }
}
