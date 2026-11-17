import { BookOpen, SearchX } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/shared/components/Button";
import { EmptyState } from "@/shared/components/EmptyState";
import type { Entry } from "@/features/review/types";
import { cn } from "@/shared/styles/cn";

import { groupByMonth } from "../../group";
import { LEDGER_COLUMNS, LedgerRow } from "../LedgerRow";

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
    <div className="flex flex-col gap-6">
      {groupByMonth(entries).map((group) => (
        <section
          key={group.key}
          aria-labelledby={`month-${group.key}`}
          className="flex flex-col gap-2"
        >
          <div className="flex items-baseline justify-between px-1 font-mono text-tiny tracking-widest text-muted-foreground uppercase">
            <h2 id={`month-${group.key}`}>{group.label}</h2>
            <p>
              {group.entries.length === 1
                ? "1 entry"
                : `${group.entries.length} entries`}
            </p>
          </div>
          <div className="overflow-hidden rounded-card border border-border bg-card">
            <div
              aria-hidden="true"
              className={cn(
                LEDGER_COLUMNS,
                "hidden border-b border-border bg-muted py-2.5 font-mono text-tiny tracking-widest text-muted-foreground uppercase lg:grid",
              )}
            >
              <span>Date</span>
              <span>Who</span>
              <span>What for</span>
              <span className="justify-self-end">Amount</span>
            </div>
            <ul className="flex flex-col divide-y divide-border">
              {group.entries.map((entry) => (
                <li key={entry.id}>
                  {entry.kind === "withholding_certificate" ? (
                    <Link
                      href={`/ledger/certificates/${entry.id}`}
                      className="block transition-colors hover:bg-muted"
                    >
                      <LedgerRow entry={entry} />
                    </Link>
                  ) : (
                    <LedgerRow entry={entry} />
                  )}
                </li>
              ))}
            </ul>
          </div>
        </section>
      ))}
    </div>
  );
}
