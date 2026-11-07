import Link from "next/link";

import type { Entry } from "@/features/review/types";
import { formatDay, formatKsh } from "@/lib/format";

/** What sits under the counterparty: the category, the date and any certificate link. */
function details(entry: Entry): string {
  const isCertificate = entry.kind === "withholding_certificate";
  const parts = [
    isCertificate ? "Withholding certificate" : (entry.category_name ?? ""),
  ];
  if (entry.occurred_on) parts.push(formatDay(entry.occurred_on));
  if (isCertificate) {
    const count = entry.linked_payment_ids?.length ?? 0;
    parts.push(
      count === 0
        ? "No payment linked"
        : count === 1
          ? "1 payment linked"
          : `${count} payments linked`,
    );
  } else if (entry.linked_certificate_id) {
    parts.push("Counted on its certificate");
  }
  return parts.filter(Boolean).join(" · ");
}

function Row({ entry }: { entry: Entry }) {
  const isIn = entry.direction === "in";
  const counted = !entry.linked_certificate_id;
  return (
    <div className="flex items-center justify-between gap-3 px-4 py-4">
      <div className="flex min-w-0 flex-col">
        <span className="truncate font-medium">
          {entry.counterparty ?? "Unknown"}
        </span>
        <span className="text-sm text-muted-foreground">{details(entry)}</span>
      </div>
      <span
        className={
          isIn && counted
            ? "shrink-0 font-bold text-money-in"
            : "shrink-0 font-bold"
        }
      >
        {isIn ? "+" : "−"}
        {formatKsh(entry.amount_cents ?? 0)}
      </span>
    </div>
  );
}

export function LedgerList({ entries }: { entries: Entry[] }) {
  if (entries.length === 0) {
    return (
      <p className="text-lg text-muted-foreground">
        Nothing confirmed here yet.
      </p>
    );
  }
  return (
    <ul className="flex flex-col divide-y divide-border rounded-3xl border border-border bg-card">
      {entries.map((entry) => (
        <li key={entry.id}>
          {entry.kind === "withholding_certificate" ? (
            <Link
              href={`/ledger/certificates/${entry.id}`}
              className="block hover:bg-muted"
            >
              <Row entry={entry} />
            </Link>
          ) : (
            <Row entry={entry} />
          )}
        </li>
      ))}
    </ul>
  );
}
