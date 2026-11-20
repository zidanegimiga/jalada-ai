import {
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname } from "node:path";

import type { Account } from "@shared/bridge";

import type { KeyProtector } from "../store/key";

/** The desktop app's session: the token the API gave it, and whose it is. */
export type SavedSession = { token: string; account: Account };

/**
 * Keeps the session between launches, sealed by the system keychain like the database key,
 * so the token is never written in plain text (decision 0029).
 */
export class SessionVault {
  constructor(
    private readonly file: string,
    private readonly protector: KeyProtector,
  ) {}

  save(session: SavedSession): void {
    mkdirSync(dirname(this.file), { recursive: true });
    writeFileSync(this.file, this.protector.seal(JSON.stringify(session)), {
      mode: 0o600,
    });
  }

  /** The saved session, or null when there is none or it cannot be read any more. */
  load(): SavedSession | null {
    if (!existsSync(this.file) || !this.protector.isSecure()) return null;
    try {
      return JSON.parse(
        this.protector.open(readFileSync(this.file)),
      ) as SavedSession;
    } catch {
      return null;
    }
  }

  clear(): void {
    rmSync(this.file, { force: true });
  }
}
