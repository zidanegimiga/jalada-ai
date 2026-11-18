"use client";

import { Check, Clock, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/shared/components/Button";
import { FormError } from "@/shared/components/FormError";

import { decide } from "../../api/agent.api";
import type { SuggestedAction } from "../../types";

const SETTLED = {
  confirmed: { Icon: Check, text: "Done" },
  declined: { Icon: X, text: "Left as it was" },
  expired: { Icon: Clock, text: "Expired. Ask again if you still want it." },
} as const;

/**
 * A change the assistant suggested, under its answer. Nothing changes until Confirm is
 * tapped; then the ledger makes the change exactly as if it were done by hand.
 */
export function ActionCard({ action }: { action: SuggestedAction }) {
  const router = useRouter();
  const [current, setCurrent] = useState(action);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // The API marks a suggestion expired when the conversation is opened, and refuses a late
  // tap with a message, so the status it gives is enough here.
  const open = current.status === "proposed";
  const status = current.status === "proposed" ? null : SETTLED[current.status];

  async function answer(decision: "confirm" | "decline") {
    setBusy(true);
    setError(null);
    try {
      setCurrent(await decide(current.id, decision));
      // To check, the ledger and the badge all show the change.
      if (decision === "confirm") router.refresh();
    } catch (problem) {
      setError(
        problem instanceof Error ? problem.message : "That did not save.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section
      aria-label="Suggested change"
      className="flex flex-col gap-3 rounded-card border border-primary/40 bg-card p-4"
    >
      <p className="font-medium">{current.summary}</p>
      {open ? (
        <div className="flex flex-wrap gap-2">
          <Button disabled={busy} onClick={() => void answer("confirm")}>
            <Check aria-hidden="true" />
            Confirm
          </Button>
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => void answer("decline")}
          >
            Not now
          </Button>
        </div>
      ) : (
        status && (
          <p className="flex items-center gap-2 text-small text-muted-foreground">
            <status.Icon aria-hidden="true" className="size-4" />
            {status.text}
          </p>
        )
      )}
      <FormError message={error} />
    </section>
  );
}
