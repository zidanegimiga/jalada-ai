import { formatDay, formatKsh } from "@/lib/format";

import type { Entry } from "@/features/review/types";

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
      {entries.map((entry) => {
        const isIn = entry.direction === "in";
        return (
          <li
            key={entry.id}
            className="flex items-center justify-between gap-3 px-4 py-4"
          >
            <div className="flex min-w-0 flex-col">
              <span className="truncate font-medium">
                {entry.counterparty ?? "Unknown"}
              </span>
              <span className="text-sm text-muted-foreground">
                {entry.category_name} ·{" "}
                {entry.occurred_on ? formatDay(entry.occurred_on) : ""}
              </span>
            </div>
            <span
              className={
                isIn ? "shrink-0 font-bold text-money-in" : "shrink-0 font-bold"
              }
            >
              {isIn ? "+" : "−"}
              {formatKsh(entry.amount_cents ?? 0)}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
