"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Amount } from "@/components/ui/amount";
import { Button } from "@/components/ui/button";
import { formatDay } from "@/lib/format";

import { markNotATransaction, sayHowPaid } from "../api";
import type { ReviewItem } from "../types";
import { NotATransaction } from "./not-a-transaction";

/** For a receipt whose payment message never arrived. The answer turns it into a payment
 * on that account, which the user then confirms. */
export function HowPaidCard({ item }: { item: ReviewItem }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const { entry, evidence } = item;
  if (!entry) return null;

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
      <header className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1">
          <p className="text-amount">
            {entry.amount_cents ? (
              <Amount cents={entry.amount_cents} />
            ) : (
              "Amount not read"
            )}
          </p>
          <p className="text-muted-foreground">
            {entry.counterparty ?? "Unknown"}
            {entry.occurred_on ? ` · ${formatDay(entry.occurred_on)}` : ""}
          </p>
        </div>
        <a
          href={`/v1/evidence/${evidence.id}/file`}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 underline underline-offset-4"
        >
          See receipt
        </a>
      </header>
      <p className="rounded-inset bg-secondary px-4 py-3 text-secondary-foreground">
        No payment message came for this receipt. How did you pay?
      </p>
      <div className="grid grid-cols-2 gap-2">
        <Button
          variant="outline"
          size="lg"
          onClick={() => answer(() => sayHowPaid(entry.id, "cash"))}
        >
          Cash
        </Button>
        <Button
          variant="outline"
          size="lg"
          onClick={() => answer(() => sayHowPaid(entry.id, "card"))}
        >
          Card
        </Button>
      </div>
      {error && (
        <p role="alert" className="text-destructive">
          {error}
        </p>
      )}
      <NotATransaction
        onConfirm={() => answer(() => markNotATransaction(evidence.id))}
      />
    </article>
  );
}
