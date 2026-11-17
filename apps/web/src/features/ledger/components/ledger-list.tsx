import { BookOpen, SearchX } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
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
        <span className="text-small text-muted-foreground">
          {details(entry)}
        </span>
      </div>
      <span
        className={
          isIn && counted
            ? "shrink-0 font-bold tabular-nums text-money-in"
            : "shrink-0 font-bold tabular-nums"
        }
      >
        {isIn ? "+" : "−"}
        {formatKsh(entry.amount_cents ?? 0)}
      </span>
    </div>
  );
}

export function LedgerList({
  entries,
  filtered = false,
}: {
  entries: Entry[];
  /** Whether a month, direction or purpose filter is on. */
  filtered?: boolean;
}) {
  if (entries.length === 0 && filtered) {
    return (
      <EmptyState
        Icon={SearchX}
        title="Nothing matches"
        action={
          <Link
            href="/ledger"
            className={buttonVariants({ variant: "outline" })}
          >
            Show everything
          </Link>
        }
      >
        <p>No confirmed entries fit these filters.</p>
      </EmptyState>
    );
  }
  if (entries.length === 0) {
    return (
      <EmptyState
        Icon={BookOpen}
        title="Your ledger is empty"
        action={
          <Link
            href="/review"
            className={buttonVariants({ variant: "outline" })}
          >
            Go to To check
          </Link>
        }
      >
        <p>
          Entries appear here once you confirm them on To check. Each one keeps
          the message or receipt it came from.
        </p>
      </EmptyState>
    );
  }
  return (
    <ul className="flex flex-col divide-y divide-border rounded-card border border-border bg-card">
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
