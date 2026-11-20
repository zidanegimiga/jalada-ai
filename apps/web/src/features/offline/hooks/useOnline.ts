"use client";

import { useSyncExternalStore } from "react";

function subscribe(changed: () => void): () => void {
  window.addEventListener("online", changed);
  window.addEventListener("offline", changed);
  return () => {
    window.removeEventListener("online", changed);
    window.removeEventListener("offline", changed);
  };
}

/**
 * Whether the browser says it has a connection. It only knows about the device's own link,
 * so true does not promise the server can be reached; false is reliable.
 */
export function useOnline(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => navigator.onLine,
    // The server always renders as online, so nothing flashes for most people.
    () => true,
  );
}
