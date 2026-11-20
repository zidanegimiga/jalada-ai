import type { Account } from "@shared/bridge";

import { newSignInRequest, readSignInLink, type SignInRequest } from "./pkce";
import type { SavedSession, SessionVault } from "./session-vault";

/** What signing in needs from the outside world, passed in so it can be tested. */
export type DeviceAuthPorts = {
  apiOrigin: string;
  webOrigin: string;
  vault: SessionVault;
  /** Opens a web page in the system browser. */
  openInBrowser: (url: string) => Promise<void>;
  /** The main process's own fetch, which only reaches the API (apply-security.ts). */
  fetch: (url: string, init: RequestInit) => Promise<Response>;
  /** Called after sign-in and sign-out, with who is signed in now. */
  changed: (account: Account | null) => void;
  /** Deletes the person's records from this computer when they sign out. */
  forgetRecords: (accountId: string) => void;
  now?: () => number;
};

/** How long a sign-in in the browser may take before the app stops waiting for it. */
export const SIGN_IN_WAIT_MS = 5 * 60 * 1000;

export class SignInFailed extends Error {}

/**
 * Signing the desktop app in through the browser, and out again (decision 0029). Only one
 * sign-in can be waiting at a time; a link that does not answer it is ignored.
 */
export class DeviceAuth {
  private pending: (SignInRequest & { startedAt: number }) | null = null;
  private session: SavedSession | null = null;

  constructor(private readonly ports: DeviceAuthPorts) {}

  /**
   * Reads the saved session back. Only once the app is ready: before that the system
   * keychain cannot be used, and the session would look missing.
   */
  restore(): Account | null {
    this.session = this.ports.vault.load();
    return this.current();
  }

  /** Whether a sign-in in the browser is still being waited for. */
  waiting(): boolean {
    return this.pending !== null && !this.expired();
  }

  /** Stops waiting for the browser; a link that arrives later is ignored. */
  cancel(): void {
    this.pending = null;
  }

  private expired(): boolean {
    return (
      this.pending !== null &&
      this.clock() - this.pending.startedAt > SIGN_IN_WAIT_MS
    );
  }

  private clock(): number {
    return this.ports.now?.() ?? Date.now();
  }

  current(): Account | null {
    return this.session?.account ?? null;
  }

  token(): string | null {
    return this.session?.token ?? null;
  }

  /** Opens the browser at the web app, which asks the person before signing the app in. */
  async start(): Promise<void> {
    this.pending = { ...newSignInRequest(), startedAt: this.clock() };
    const page = new URL("/desktop/sign-in", this.ports.webOrigin);
    page.searchParams.set("challenge", this.pending.challenge);
    page.searchParams.set("state", this.pending.state);
    await this.ports.openInBrowser(page.href);
  }

  /**
   * Finishes sign-in with the `jalada://signed-in` link, opened by the browser or pasted by
   * the person when the browser could not open the app. Either way it must answer this
   * app's own request, made in the last few minutes.
   */
  async finish(link: string): Promise<Account> {
    const answer = readSignInLink(link.trim());
    if (this.expired()) {
      this.pending = null;
      throw new SignInFailed(
        "That sign-in took too long. Start again from the app.",
      );
    }
    const pending = this.pending;
    if (!answer || !pending || answer.state !== pending.state) {
      throw new SignInFailed(
        "That link does not answer a sign-in from this app.",
      );
    }
    this.pending = null;
    const response = await this.ports.fetch(
      `${this.ports.apiOrigin}/v1/auth/device/token`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: answer.code, verifier: pending.verifier }),
      },
    );
    if (!response.ok)
      throw new SignInFailed("The server did not accept the sign-in.");
    const body = (await response.json()) as {
      token: string;
      user: { id: string; email: string; display_name: string };
    };
    const account = {
      id: body.user.id,
      email: body.user.email,
      name: body.user.display_name,
    };
    this.session = { token: body.token, account };
    this.ports.vault.save(this.session);
    this.ports.changed(account);
    return account;
  }

  /** Ends the session on the server when it can, and always on this computer. */
  async signOut(): Promise<void> {
    const session = this.session;
    if (!session) return;
    this.session = null;
    this.ports.vault.clear();
    // Told first, so the records are closed before their files are deleted.
    this.ports.changed(null);
    this.ports.forgetRecords(session.account.id);
    try {
      await this.ports.fetch(`${this.ports.apiOrigin}/v1/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.token}` },
      });
    } catch {
      // Offline: the session expires on the server by itself; nothing is left here.
    }
  }
}
