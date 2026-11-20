"use client";

import { Wifi, WifiOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { useOnline } from "../../hooks/useOnline";

/** How long "Back online" stays before it slides away. */
const BACK_FOR_MS = 3000;

/**
 * A strip under the header while the device is offline, saying what still works, and a
 * short "Back online" when the connection returns. Read out by screen readers as it changes.
 */
export function ConnectionStatus() {
  const online = useOnline();
  const wasOffline = useRef(false);
  const [back, setBack] = useState(false);

  useEffect(() => {
    if (!online) {
      wasOffline.current = true;
      return;
    }
    if (!wasOffline.current) return;
    wasOffline.current = false;
    const show = setTimeout(() => setBack(true), 0);
    const hide = setTimeout(() => setBack(false), BACK_FOR_MS);
    return () => {
      clearTimeout(show);
      clearTimeout(hide);
    };
  }, [online]);

  return (
    <div role="status" aria-live="polite" className="contents">
      {!online && (
        <p className="flex items-center gap-2 bg-secondary px-gutter py-2 text-small text-secondary-foreground">
          <WifiOff aria-hidden="true" className="size-4 shrink-0" />
          You are offline. What is on screen stays; saving waits for a
          connection.
        </p>
      )}
      {online && back && (
        <p className="flex items-center gap-2 bg-muted px-gutter py-2 text-small">
          <Wifi aria-hidden="true" className="size-4 shrink-0" />
          Back online.
        </p>
      )}
    </div>
  );
}
