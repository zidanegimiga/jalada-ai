"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { EvidenceItem } from "../api";

type Notice = { tone: "success" | "error"; text: string };

/** Runs an upload or paste, reports the outcome, and refreshes the list. */
export function useCapture() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);

  async function run(action: () => Promise<EvidenceItem>): Promise<boolean> {
    setBusy(true);
    setNotice(null);
    try {
      const item = await action();
      setNotice({
        tone: "success",
        text: item.duplicate ? "You already sent this one." : "Saved.",
      });
      router.refresh();
      return true;
    } catch (error) {
      setNotice({ tone: "error", text: (error as Error).message });
      return false;
    } finally {
      setBusy(false);
    }
  }

  return { busy, notice, run };
}
