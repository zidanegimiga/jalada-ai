import { net } from "electron";

import type { Connection } from "@shared/bridge";

/** How often the connection is checked while the app is open. */
const CHECK_EVERY_MS = 5000;

/**
 * Watches whether the computer is online and reports changes. Electron's `net.isOnline`
 * only knows about the computer's own link; the sync engine finds out whether the server
 * itself can be reached.
 */
export function watchConnection(
  changed: (connection: Connection) => void,
): () => void {
  let last: Connection = current();
  const timer = setInterval(() => {
    const now = current();
    if (now === last) return;
    last = now;
    changed(now);
  }, CHECK_EVERY_MS);
  return () => clearInterval(timer);
}

export function current(): Connection {
  return net.isOnline() ? "online" : "offline";
}
