import { useCallback, useEffect, useState } from "react";

import type { LocalChange } from "@shared/records";

/** The changes made on this computer, kept up to date as they are sent. */
export function useChanges() {
  const [changes, setChanges] = useState<LocalChange[]>([]);
  const [unsent, setUnsent] = useState(0);

  const load = useCallback(async () => {
    const [rows, waiting] = await Promise.all([
      window.jalada.changes.list(),
      window.jalada.changes.unsent(),
    ]);
    setChanges(rows);
    setUnsent(waiting);
  }, []);

  useEffect(() => {
    void load();
    return window.jalada.changes.onChange(() => void load());
  }, [load]);

  return {
    changes,
    unsent,
    pasteMessage: (text: string) => window.jalada.changes.pasteMessage(text),
    actions: {
      tryAgain: (id: string) => void window.jalada.changes.tryAgain(id),
      discard: (id: string) => void window.jalada.changes.discard(id),
    },
  };
}
