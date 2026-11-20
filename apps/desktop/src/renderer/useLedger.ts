import { useCallback, useEffect, useState } from "react";

import type { LedgerStatus } from "@shared/bridge";
import type { LocalEntry } from "@shared/records";

const PAGE = 100;

/**
 * The ledger as this computer holds it, refreshed whenever the main process reports a
 * change. It never waits on the network, so it shows the same offline as online.
 */
export function useLedger() {
  const [entries, setEntries] = useState<LocalEntry[]>([]);
  const [status, setStatus] = useState<LedgerStatus | null>(null);

  const load = useCallback(async () => {
    const [rows, now] = await Promise.all([
      window.jalada.ledger.list(PAGE, 0),
      window.jalada.ledger.status(),
    ]);
    setEntries(rows);
    setStatus(now);
  }, []);

  useEffect(() => {
    void load();
    return window.jalada.ledger.onChange(() => void load());
  }, [load]);

  return {
    entries,
    status,
    refresh: () => void window.jalada.ledger.refresh(),
  };
}
