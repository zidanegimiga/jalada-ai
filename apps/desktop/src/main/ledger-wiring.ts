import { randomUUID } from "node:crypto";

import { ipcMain, net } from "electron";

import { CHANNELS, type Connection } from "@shared/bridge";

import type { DeviceAuth } from "./auth/device-auth";
import type { DesktopConfig } from "./config";
import { current } from "./connection";
import type { LocalStore } from "./store/local-store";
import { LedgerSync } from "./sync/ledger-sync";
import { sendToWindows } from "./windows";

/** How often the ledger is refreshed while the app is open and online. */
const REFRESH_EVERY_MS = 10 * 60 * 1000;
/** How often changes the server did not take yet are tried again, while online. */
const RETRY_CHANGES_EVERY_MS = 60 * 1000;

const SESSION_ENDED =
  "Your session has ended. Sign in again to keep your records here.";

/**
 * The ledger on this computer (decision 0029): answers the window's questions from the
 * local copy, and refreshes it from the server. `auth` is asked for lazily, since sign-in and
 * the ledger each need the other.
 */
export function wireLedger(
  config: DesktopConfig,
  store: LocalStore,
  auth: () => DeviceAuth,
): LedgerSync {
  const ledger = new LedgerSync({
    apiOrigin: config.apiOrigin,
    store,
    fetch: (url, init) => net.fetch(url, init),
    token: () => auth().token(),
    sessionEnded: () => {
      sendToWindows(CHANNELS.signInFailed, SESSION_ENDED);
      void auth().signOut();
    },
    changed: (status) => sendToWindows(CHANNELS.ledgerChanged, status),
    changesChanged: () => sendToWindows(CHANNELS.changesChanged, null),
    newId: randomUUID,
    failed: (message) => sendToWindows(CHANNELS.signInFailed, message),
  });

  ipcMain.handle(
    CHANNELS.ledgerList,
    (_event, limit: unknown, offset: unknown) =>
      ledger.list(
        Math.min(Math.max(Number(limit) || 50, 1), 200),
        Math.max(Number(offset) || 0, 0),
      ),
  );
  ipcMain.handle(CHANNELS.ledgerStatus, () => ledger.status());
  ipcMain.handle(CHANNELS.ledgerRefresh, () => ledger.pull());
  ipcMain.handle(CHANNELS.changesPaste, (_event, text: unknown) =>
    ledger.addChange("pasted_message", text),
  );
  ipcMain.handle(CHANNELS.changesList, () => ledger.changes());
  ipcMain.handle(CHANNELS.changesUnsent, () => ledger.unsent());
  return ledger;
}

/**
 * Once the app is ready, and before the window opens: restores the saved session, opens
 * that person's records and keeps them fresh.
 */
export function startLedger(
  ledger: LedgerSync,
  auth: DeviceAuth,
): (connection: Connection) => void {
  ledger.switchTo(auth.restore());
  setInterval(() => {
    if (current() === "online") void ledger.pull();
  }, REFRESH_EVERY_MS);
  setInterval(() => {
    if (current() === "online" && ledger.unsent() > 0) void ledger.pull();
  }, RETRY_CHANGES_EVERY_MS);
  // Back online: catch up straight away.
  return (connection) => {
    if (connection === "online") void ledger.pull();
  };
}
