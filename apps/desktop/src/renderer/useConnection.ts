import { useEffect, useState } from "react";

import type { Connection } from "@shared/bridge";

/** Whether the computer is online, as the main process sees it, kept up to date. */
export function useConnection(): Connection | null {
  const [connection, setConnection] = useState<Connection | null>(null);
  useEffect(() => {
    let live = true;
    void window.jalada.connection.current().then((now) => {
      if (live) setConnection(now);
    });
    const stop = window.jalada.connection.onChange(setConnection);
    return () => {
      live = false;
      stop();
    };
  }, []);
  return connection;
}
