"use client";

import { useId, useState } from "react";

import { ActionButton } from "@/shared/components/ActionButton";
import { Button } from "@/shared/components/Button";
import { DatePicker } from "@/shared/components/DatePicker";
import { FormField } from "@/features/auth/components/FormField";
import { Select } from "@/shared/components/Select";
import { centsToInput } from "@/shared/format/format";

import type { Category, Entry, EntryValues } from "../../types";

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
      <DatePicker
        label="Date"
        name="occurred_on"
        defaultValue={entry?.occurred_on ?? ""}
      />
      <FormField
        label="Paid to or received from"
        name="counterparty"
        id={`${id}-counterparty`}
        maxLength={200}
        defaultValue={entry?.counterparty ?? ""}
      />
      <Select
        key={direction}
        label="What it was for"
        name="category"
        required
        options={choices.map((category) => ({
          value: category.slug,
          label: category.name,
        }))}
        defaultValue={keptCategory || null}
      />
      <ActionButton type="submit" busy={busy}>
        {busy ? "Saving..." : submitLabel}
      </ActionButton>
    </form>
  );
}
