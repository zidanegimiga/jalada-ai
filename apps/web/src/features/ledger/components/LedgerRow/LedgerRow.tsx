import type { Entry } from "@/features/review/types";
import { formatDay, formatKsh } from "@/shared/format/format";
import { cn } from "@/shared/styles/cn";

/**
 * The columns of a ledger row. On a phone: who it was with and the amount, with the details
 * underneath. On a wide screen: date, who, what for and amount, like a table.
 */
export const LEDGER_COLUMNS =
  "grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-0.5 px-4 lg:grid-cols-[6rem_minmax(0,1fr)_minmax(0,10rem)_8rem] lg:px-5";

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

export function LedgerRow({ entry }: { entry: Entry }) {
  const isIn = entry.direction === "in";
  const counted = !entry.linked_certificate_id;
  return (
    <div className={cn(LEDGER_COLUMNS, "py-4 lg:py-3.5")}>
      <span className="hidden text-small text-muted-foreground tabular-nums lg:block">
        {entry.occurred_on ? formatDay(entry.occurred_on) : ""}
      </span>
      <span
        title={entry.counterparty ?? undefined}
        className="truncate font-medium"
      >
        {entry.counterparty ?? "Unknown"}
      </span>
      <span
        title={purpose(entry)}
        className="hidden truncate text-small text-muted-foreground lg:block"
      >
        {purpose(entry)}
      </span>
      <span
        className={cn(
          "justify-self-end font-bold whitespace-nowrap tabular-nums",
          isIn && counted && "text-money-in",
        )}
      >
        {isIn ? "+" : "−"}
        {formatKsh(entry.amount_cents ?? 0)}
      </span>
      <span className="col-span-2 text-small text-muted-foreground lg:hidden">
        {details(entry)}
      </span>
    </div>
  );
}
