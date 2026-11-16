"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { formatDay, formatKsh } from "@/lib/format";

import { acceptMatch, declineMatch } from "../api";
import type { ReviewItem } from "../types";

type Side = {
  label: string;
  amountCents: number | null;
  counterparty: string | null;
  occurredOn: string | null;
  href: string;
  linkLabel: string;
};

/** "Same amount, same day" from the reasons the API gives. */
function describeReasons(reasons: string[]) {
  const sentence = reasons.join(", ");
  return sentence.charAt(0).toUpperCase() + sentence.slice(1);
}

function SideOf({ side }: { side: Side }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-inset bg-secondary px-4 py-3 text-secondary-foreground">
      <div className="flex flex-col gap-1">
        <p className="text-small text-muted-foreground">{side.label}</p>
        <p className="font-bold">
          {side.amountCents ? formatKsh(side.amountCents) : "Amount not read"}
        </p>
        <p>
          {side.counterparty ?? "Unknown"}
          {side.occurredOn ? ` · ${formatDay(side.occurredOn)}` : ""}
        </p>
      </div>
      <a
        href={side.href}
        target="_blank"
        rel="noreferrer"
        className="shrink-0 underline underline-offset-4"
      >
        {side.linkLabel}
      </a>
    </div>
  );
}

/** Asks if a receipt and a payment are the same purchase. Nothing is joined until the
 * user says yes, and a no is never asked again. */
export function MatchCard({ item }: { item: ReviewItem }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const { entry, evidence, match } = item;
  if (!entry || !match) return null;

  async function answer(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
      router.refresh();
    } catch (caught) {
      setError((caught as Error).message);
    }
  }

  return (
    <article className="flex flex-col gap-4 rounded-card border border-border bg-card p-card">
      <h2 className="text-title">
        We found a receipt that may belong to this payment
      </h2>
      <SideOf
        side={{
          label: "Payment",
          amountCents: entry.amount_cents,
          counterparty: entry.counterparty,
          occurredOn: entry.occurred_on,
          href: `/v1/evidence/${evidence.id}/file`,
          linkLabel: "See payment",
        }}
      />
      <SideOf
        side={{
          label: "Receipt",
          amountCents: match.amount_cents,
          counterparty: match.counterparty,
          occurredOn: match.occurred_on,
          href: `/v1/evidence/${match.receipt.id}/file`,
          linkLabel: "See receipt",
        }}
      />
      <p className="text-muted-foreground">{describeReasons(match.reasons)}</p>
      <div className="grid grid-cols-2 gap-2">
        <Button
          variant="outline"
          size="lg"
          onClick={() => answer(() => declineMatch(match.suggestion_id))}
        >
          Not the same
        </Button>
        <Button
          size="lg"
          onClick={() => answer(() => acceptMatch(match.suggestion_id))}
        >
          Yes, same purchase
        </Button>
      </div>
      {error && (
        <p role="alert" className="text-destructive">
          {error}
        </p>
      )}
    </article>
  );
}
