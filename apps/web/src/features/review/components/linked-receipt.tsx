"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";

import { undoMatch } from "../api";
import type { ReviewItem } from "../types";

type Match = NonNullable<ReviewItem["linked_receipt"]>;

/** A receipt the user joined to this payment, with a way to take that back. */
export function LinkedReceipt({ match }: { match: Match }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  async function undo() {
    setError(null);
    try {
      await undoMatch(match.suggestion_id);
      router.refresh();
    } catch (caught) {
      setError((caught as Error).message);
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-border px-4 py-3">
      <div className="flex items-center justify-between gap-3">
        <p>
          Receipt from {match.counterparty ?? "an unknown shop"} is linked.{" "}
          <a
            href={`/v1/evidence/${match.receipt.id}/file`}
            target="_blank"
            rel="noreferrer"
            className="underline underline-offset-4"
          >
            See receipt
          </a>
        </p>
        <Button variant="ghost" onClick={undo}>
          Undo
        </Button>
      </div>
      {error && (
        <p role="alert" className="text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
