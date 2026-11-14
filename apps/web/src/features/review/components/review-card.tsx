"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { formatDay, formatKsh } from "@/lib/format";

import {
  confirmEntry,
  correctEntry,
  enterByHand,
  markNotATransaction,
} from "../api";
import type { Category, EntryValues, ReviewItem } from "../types";
import { EntryForm } from "./entry-form";
import { NotATransaction } from "./not-a-transaction";

export function ReviewCard({
  item,
  categories,
}: {
  item: ReviewItem;
  categories: Category[];
}) {
  const router = useRouter();
  const { entry, evidence } = item;
  const [editing, setEditing] = useState(entry === null);
  const [error, setError] = useState<string | null>(null);

  async function run(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
      router.refresh();
    } catch (caught) {
      setError((caught as Error).message);
    }
  }

  function save(values: EntryValues) {
    return run(() =>
      entry ? correctEntry(entry.id, values) : enterByHand(evidence.id, values),
    );
  }

  return (
    <article className="flex flex-col gap-4 rounded-3xl border border-border bg-card p-5">
      <header className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1">
          <p className="text-2xl font-bold">
            {entry?.amount_cents
              ? formatKsh(entry.amount_cents)
              : "Amount not read"}
          </p>
          <p className="text-muted-foreground">
            {entry?.counterparty ?? "Unknown"}
            {entry?.occurred_on ? ` · ${formatDay(entry.occurred_on)}` : ""}
          </p>
        </div>
        <a
          href={`/v1/evidence/${evidence.id}/file`}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 underline underline-offset-4"
        >
          See original
        </a>
      </header>
      {entry && !editing && (
        <>
          <p className="rounded-2xl bg-secondary px-4 py-3 text-secondary-foreground">
            {entry.category_name
              ? entry.category_name
              : "We could not tell what this was for."}
          </p>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              size="lg"
              onClick={() => setEditing(true)}
            >
              Change
            </Button>
            <Button
              size="lg"
              onClick={() =>
                entry.category
                  ? run(() => confirmEntry(entry.id))
                  : setEditing(true)
              }
            >
              Confirm
            </Button>
          </div>
        </>
      )}
      {editing && (
        <EntryForm
          entry={entry}
          categories={categories}
          onSubmit={save}
          submitLabel={entry ? "Save and confirm" : "Add to ledger"}
        />
      )}
      {error && (
        <p role="alert" className="text-destructive">
          {error}
        </p>
      )}
      <NotATransaction
        onConfirm={() => run(() => markNotATransaction(evidence.id))}
      />
    </article>
  );
}
