import { ArrowLeftRight } from "lucide-react";

import type { Entry } from "@/features/review/types";
import { Amount } from "@/shared/components/Amount";
import { FolderCard } from "@/shared/components/FolderCard";
import { formatDay } from "@/shared/format/format";

import { isTransfer } from "../LedgerRow";

/** The payment at a glance: which way, how much, with whom and when. */
export function EntryHeader({ entry }: { entry: Entry }) {
  const transfer = isTransfer(entry);
  const tab = transfer
    ? "Transfer"
    : entry.direction === "in"
      ? "Money in"
      : "Money out";
  return (
    <FolderCard tab={tab} aria-labelledby="entry-heading" className="gap-3">
      <h1 id="entry-heading" className="text-display break-words">
        {entry.counterparty ?? "Unknown"}
      </h1>
      <p className="flex items-center gap-2 text-total">
        {transfer ? (
          <ArrowLeftRight
            aria-hidden="true"
            className="size-icon-lg opacity-70"
          />
        ) : (
          <span aria-hidden="true" className="opacity-70">
            {entry.direction === "in" ? "+" : "−"}
          </span>
        )}
        <Amount cents={entry.amount_cents ?? 0} fadeCents />
      </p>
      <p className="opacity-75">
        {entry.occurred_on ? formatDay(entry.occurred_on) : "No date"}
        {transfer && " · Between your own accounts, not counted in totals"}
      </p>
    </FolderCard>
  );
}
