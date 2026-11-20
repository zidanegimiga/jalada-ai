import { randomBytes } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname } from "node:path";

/**
 * Whatever keeps a secret safe on this computer: the system keychain in the app
 * (`safeStorage`), a fake in tests (decision 0029).
 */
export type KeyProtector = {
  /** False when the system has no secure store, so the key would sit in plain text. */
  isSecure: () => boolean;
  seal: (secret: string) => Buffer;
  open: (sealed: Buffer) => string;
};

export class NoSecureStore extends Error {
  constructor() {
    super(
      "This computer has no secure place for the database key, so records are not kept on it.",
    );
  }
}

/**
 * The database key for one person: 32 random bytes, kept in `file` sealed by the system
 * keychain. Made on first use. Never written anywhere in plain text.
 */
export function loadOrCreateKey(file: string, protector: KeyProtector): string {
  if (!protector.isSecure()) throw new NoSecureStore();
  if (existsSync(file)) return protector.open(readFileSync(file));
  const key = randomBytes(32).toString("hex");
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, protector.seal(key), { mode: 0o600 });
  return key;
}

export function forgetKey(file: string): void {
  rmSync(file, { force: true });
}
