/**
 * Everything the window may ask of the main process, and nothing more (decision 0029).
 * The preload script puts an object of this shape on `window.jalada`; the window never
 * reaches Node.js, the file system or the network itself.
 */
import type { LocalEntry } from "./records";

export type Connection = "online" | "offline";

export type AppInfo = {
  version: string;
  /** The server the app syncs with, shown so people know where their records go. */
  apiOrigin: string;
};

/** The ledger on this computer: how much is here, and how fresh it is. */
export type LedgerStatus = {
  entries: number;
  /** When it was last copied from the server, or null if never. */
  updatedAt: string | null;
  updating: boolean;
};

/** Who is signed in on this computer. */
export type Account = { id: string; email: string; name: string };

export type JaladaBridge = {
  app: { info: () => Promise<AppInfo> };
  connection: {
    current: () => Promise<Connection>;
    /** Calls back whenever the connection changes. Returns a function that stops it. */
    onChange: (changed: (connection: Connection) => void) => () => void;
  };
  account: {
    current: () => Promise<Account | null>;
    /** Opens the browser to sign in; the answer arrives through `onChange`. */
    signIn: () => Promise<void>;
    signOut: () => Promise<void>;
    onChange: (changed: (account: Account | null) => void) => () => void;
    /** Calls back when a sign-in through the browser fails. */
    onFailed: (failed: (message: string) => void) => () => void;
  };
  ledger: {
    /** Entries from this computer's copy, newest first. Works offline. */
    list: (limit: number, offset: number) => Promise<LocalEntry[]>;
    status: () => Promise<LedgerStatus>;
    /** Asks for a fresh copy from the server now. */
    refresh: () => Promise<void>;
    onChange: (changed: (status: LedgerStatus) => void) => () => void;
  };
};

/** The names of the messages between the bridge and the main process. */
export const CHANNELS = {
  appInfo: "app:info",
  connection: "connection:current",
  connectionChanged: "connection:changed",
  account: "account:current",
  signIn: "account:sign-in",
  signOut: "account:sign-out",
  accountChanged: "account:changed",
  signInFailed: "account:sign-in-failed",
  ledgerList: "ledger:list",
  ledgerStatus: "ledger:status",
  ledgerRefresh: "ledger:refresh",
  ledgerChanged: "ledger:changed",
} as const;
