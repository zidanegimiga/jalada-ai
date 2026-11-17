"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { EvidenceDialog } from "@/features/evidence/components/EvidenceDialog";
import { Amount } from "@/shared/components/Amount";
import { Button } from "@/shared/components/Button";
import { FormError } from "@/shared/components/FormError";
import { formatDay } from "@/shared/format/format";

import {
  confirmEntry,
  correctEntry,
  enterByHand,
  markNotATransaction,
} from "../../api/review.api";
import type { Category, EntryValues, ReviewItem } from "../../types";
import { EntryForm } from "../EntryForm";
import { LinkedReceipt } from "../LinkedReceipt";
import { NotATransaction } from "../NotATransaction";
import { OwnAccountNote } from "../OwnAccountNote";
import { OwnAccountQuestion } from "../OwnAccountQuestion";

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
    <article className="flex flex-col gap-4 rounded-card border border-border bg-card p-card">
      <header className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1">
          <p className="text-amount">
            {entry?.amount_cents ? (
              <Amount cents={entry.amount_cents} fadeCents />
            ) : (
              "Amount not read"
            )}
          </p>
          <p className="text-muted-foreground">
            {entry?.counterparty ?? "Unknown"}
            {entry?.occurred_on ? ` · ${formatDay(entry.occurred_on)}` : ""}
          </p>
        </div>
        <EvidenceDialog
          evidenceId={evidence.id}
          contentType={evidence.content_type}
          trigger={
            <button
              type="button"
              className="inline-flex min-h-tap shrink-0 items-center underline underline-offset-4"
            >
              See original
            </button>
          }
        />
      </header>
      {item.linked_receipt && <LinkedReceipt match={item.linked_receipt} />}
      {entry && item.own_account && !editing && (
        <OwnAccountNote
          entryId={entry.id}
          account={item.own_account}
          direction={entry.direction === "in" ? "in" : "out"}
        />
      )}
      {entry && item.ask_own_account && !editing && (
        <OwnAccountQuestion
          entryId={entry.id}
          direction={entry.direction === "in" ? "in" : "out"}
        />
      )}
      {entry && !editing && (
        <>
          <p className="rounded-inset bg-secondary px-4 py-3 text-secondary-foreground">
            {!entry.category_name
              ? "We could not tell what this was for."
              : entry.category_suggested
                ? `Suggested: ${entry.category_name}. Is that right?`
                : entry.category_name}
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
              {entry.category_suggested ? "Yes, confirm" : "Confirm"}
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
      <FormError message={error} />
      <NotATransaction
        onConfirm={() => run(() => markNotATransaction(evidence.id))}
      />
    </article>
  );
}
