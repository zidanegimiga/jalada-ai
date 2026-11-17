"use client";

import { Pencil } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/shared/components/Button";
import { FormError } from "@/shared/components/FormError";

import { correctEntry } from "../../api/review.api";
import type { Category, Entry, EntryValues } from "../../types";
import { EntryForm } from "../EntryForm";

/**
 * Changing a confirmed payment from its own page. The change is saved like a correction on
 * To check: it shows in the payment's history, and a new category is remembered for next time.
 */
export function EditEntry({
  entry,
  categories,
}: {
  entry: Entry;
  categories: Category[];
}) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function save(values: EntryValues) {
    setError(null);
    try {
      await correctEntry(entry.id, values);
      setEditing(false);
      setSaved(true);
      router.refresh();
    } catch (caught) {
      setError((caught as Error).message);
    }
  }

  if (!editing) {
    return (
      <div className="flex flex-col gap-2">
        <Button
          variant="outline"
          size="lg"
          onClick={() => {
            setSaved(false);
            setEditing(true);
          }}
        >
          <Pencil aria-hidden="true" />
          Edit this payment
        </Button>
        <p
          role="status"
          className="text-center text-small text-muted-foreground"
        >
          {saved ? "Saved. The change is in the history below." : ""}
        </p>
      </div>
    );
  }

  return (
    <section
      aria-labelledby="edit-heading"
      className="flex flex-col gap-4 rounded-card border border-border bg-card p-card motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2"
    >
      <div className="flex flex-col gap-1">
        <h2 id="edit-heading" className="text-title">
          Edit this payment
        </h2>
        <p className="text-muted-foreground">
          The change is kept in the history, and a new category is remembered
          for next time.
        </p>
      </div>
      <EntryForm
        entry={entry}
        categories={categories}
        submitLabel="Save changes"
        onSubmit={save}
      />
      <FormError message={error} />
      <Button variant="ghost" size="lg" onClick={() => setEditing(false)}>
        Cancel
      </Button>
    </section>
  );
}
