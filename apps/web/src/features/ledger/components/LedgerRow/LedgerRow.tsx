import { ArrowLeftRight } from "lucide-react";

import type { Entry } from "@/features/review/types";
import { formatDay, formatKsh } from "@/shared/format/format";
import { cn } from "@/shared/styles/cn";

/**
 * The columns of a ledger row. On a phone: who it was with and the amount, with the details
 * underneath. On a wide screen: date, who, what for and amount, like a table.
 */
export const LEDGER_COLUMNS =
  "grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-0.5 px-4 lg:grid-cols-[6rem_minmax(0,1fr)_minmax(0,10rem)_8rem] lg:px-5";

/**
 * The categories that make a payment a move between the person's own accounts. Such money is
 * neither in nor out, so the totals and charts leave it out (as the API's transfers do).
 */
const TRANSFER_CATEGORIES = new Set(["own_transfer", "own_transfer_out"]);

export function isTransfer(entry: Entry): boolean {
  return TRANSFER_CATEGORIES.has(entry.category ?? "");
}

const NOT_COUNTED = "Not counted in totals";

/** What it was for, and how a certificate and its payments relate. */
function purpose(entry: Entry): string {
  if (entry.kind === "withholding_certificate") {
    const count = entry.linked_payment_ids?.length ?? 0;
    const linked =
      count === 0
        ? "No payment linked"
        : count === 1
          ? "1 payment linked"
          : `${count} payments linked`;
    return `Withholding certificate · ${linked}`;
  }
  const parts = [entry.category_name ?? ""];
  if (entry.linked_certificate_id) parts.push("Counted on its certificate");
  if (isTransfer(entry)) parts.push(NOT_COUNTED);
  return parts.filter(Boolean).join(" · ");
}

/** The line under a phone row: what it was for and the date. */
function details(entry: Entry): string {
  const isCertificate = entry.kind === "withholding_certificate";
  const parts = [
    isCertificate ? "Withholding certificate" : (entry.category_name ?? ""),
  ];
  if (entry.occurred_on) parts.push(formatDay(entry.occurred_on));
  const rest = purpose(entry).split(" · ").slice(1);
  return [...parts, ...rest].filter(Boolean).join(" · ");
}

/** The name with the searched words marked, wherever they appear and in any case. */
function Marked({ text, search }: { text: string; search?: string }) {
  const words = search?.trim();
  const at = words ? text.toLowerCase().indexOf(words.toLowerCase()) : -1;
  if (!words || at < 0) return <>{text}</>;
  return (
    <>
      {text.slice(0, at)}
      <mark className="rounded-[0.2rem] bg-(--flax) px-0.5 text-(--black)">
        {text.slice(at, at + words.length)}
      </mark>
      {text.slice(at + words.length)}
    </>
  );
}

export function LedgerRow({
  entry,
  search,
}: {
  entry: Entry;
  search?: string;
}) {
  const isIn = entry.direction === "in";
  const counted = !entry.linked_certificate_id;
  const transfer = isTransfer(entry);
  return (
    <div className={cn(LEDGER_COLUMNS, "py-4 lg:py-3.5")}>
      <span className="hidden text-small text-muted-foreground tabular-nums lg:block">
        {entry.occurred_on ? formatDay(entry.occurred_on) : ""}
      </span>
      <span
        title={entry.counterparty ?? undefined}
        className={cn(
          "truncate font-medium",
          transfer && "text-muted-foreground",
        )}
      >
        <Marked text={entry.counterparty ?? "Unknown"} search={search} />
      </span>
      <span
        title={purpose(entry)}
        className="hidden truncate text-small text-muted-foreground lg:block"
      >
        {purpose(entry)}
      </span>
      {transfer ? (
        <span className="flex items-center gap-1.5 justify-self-end font-medium whitespace-nowrap text-muted-foreground tabular-nums">
          <ArrowLeftRight aria-hidden="true" className="size-4" />
          {formatKsh(entry.amount_cents ?? 0)}
        </span>
      ) : (
        <span
          className={cn(
            "justify-self-end font-bold whitespace-nowrap tabular-nums",
            isIn && counted && "text-money-in",
          )}
        >
          {isIn ? "+" : "−"}
          {formatKsh(entry.amount_cents ?? 0)}
        </span>
      )}
      <span className="col-span-2 text-small text-muted-foreground lg:hidden">
        {details(entry)}
      </span>
    </div>
  );
}
