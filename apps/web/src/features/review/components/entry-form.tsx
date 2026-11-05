"use client";

import { useId, useState } from "react";

import { Button } from "@/components/ui/button";
import { FormField } from "@/features/auth/components/form-field";
import { Label } from "@/components/ui/label";
import { centsToInput } from "@/lib/format";

import type { Category, Entry, EntryValues } from "../types";

type EntryFormProps = {
  entry: Entry | null;
  categories: Category[];
  submitLabel: string;
  onSubmit: (values: EntryValues) => Promise<void>;
};

export function EntryForm({
  entry,
  categories,
  submitLabel,
  onSubmit,
}: EntryFormProps) {
  const [direction, setDirection] = useState<"in" | "out">(
    entry?.direction ?? "out",
  );
  const [busy, setBusy] = useState(false);
  // Several cards can show this form at once, so every id gets a prefix of its own.
  const id = useId();
  const choices = categories.filter(
    (category) => category.direction === direction,
  );
  const keptCategory = choices.some((c) => c.slug === entry?.category)
    ? entry?.category
    : "";

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    try {
      await onSubmit({
        occurred_on: String(form.get("occurred_on")),
        amount: String(form.get("amount")).replace(/[^0-9.,]/g, ""),
        direction,
        counterparty: String(form.get("counterparty")),
        category: String(form.get("category")),
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      <div role="group" aria-label="Money" className="grid grid-cols-2 gap-2">
        {(["out", "in"] as const).map((value) => (
          <Button
            key={value}
            type="button"
            variant={direction === value ? "default" : "outline"}
            aria-pressed={direction === value}
            onClick={() => setDirection(value)}
          >
            {value === "out" ? "Money out" : "Money in"}
          </Button>
        ))}
      </div>
      <FormField
        label="Amount (KSh)"
        name="amount"
        id={`${id}-amount`}
        inputMode="decimal"
        placeholder="1,250.00"
        defaultValue={
          entry?.amount_cents ? centsToInput(entry.amount_cents) : ""
        }
      />
      <FormField
        label="Date"
        name="occurred_on"
        id={`${id}-occurred_on`}
        type="date"
        defaultValue={entry?.occurred_on ?? ""}
      />
      <FormField
        label="Paid to or received from"
        name="counterparty"
        id={`${id}-counterparty`}
        maxLength={200}
        defaultValue={entry?.counterparty ?? ""}
      />
      <div className="flex flex-col gap-2">
        <Label htmlFor={`${id}-category`}>What it was for</Label>
        <select
          id={`${id}-category`}
          name="category"
          required
          defaultValue={keptCategory ?? ""}
          key={direction}
          className="h-12 rounded-xl border border-input bg-card px-4 text-base"
        >
          <option value="" disabled>
            Choose one
          </option>
          {choices.map((category) => (
            <option key={category.slug} value={category.slug}>
              {category.name}
            </option>
          ))}
        </select>
      </div>
      <Button type="submit" size="lg" disabled={busy}>
        {busy ? "Saving..." : submitLabel}
      </Button>
    </form>
  );
}
