"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { formatKsh } from "@/lib/format";

import { confirmAll } from "../api";
import type { Entry } from "../types";

function total(entries: Entry[], direction: "in" | "out"): number {
  return entries
    .filter((entry) => entry.direction === direction)
    .reduce((sum, entry) => sum + (entry.amount_cents ?? 0), 0);
}

/** "3 payments are ready: KSh 1,200.00 out, KSh 500.00 in." */
function summary(entries: Entry[]): string {
  const totals = [
    [total(entries, "out"), "out"],
    [total(entries, "in"), "in"],
  ] as const;
  const parts = totals
    .filter(([cents]) => cents > 0)
    .map(([cents, way]) => `${formatKsh(cents)} ${way}`);
  return `${entries.length} payments are ready: ${parts.join(", ")}.`;
}

function stillWaiting(count: number): string {
  return count === 1
    ? "1 payment changed and still needs a look."
    : `${count} payments changed and still need a look.`;
}

/** Confirms every payment listed under it in one tap. Only those ids are sent. */
export function ConfirmAll({ entries }: { entries: Entry[] }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [skipped, setSkipped] = useState(0);
  const [busy, setBusy] = useState(false);

  async function confirm() {
    setError(null);
    setBusy(true);
    try {
      const done = await confirmAll(entries.map((entry) => entry.id));
      setSkipped(entries.length - done.confirmed.length);
      router.refresh();
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-card bg-secondary p-card text-secondary-foreground">
      <p>
        {summary(entries)} Check the list below, then confirm them together.
      </p>
      <Button onClick={confirm} disabled={busy} className="self-start">
        Confirm all {entries.length}
      </Button>
      {skipped > 0 && <p role="status">{stillWaiting(skipped)}</p>}
      {error && (
        <p role="alert" className="text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
