import type { Entry } from "@/features/review/types";

export type MonthGroup = { key: string; label: string; entries: Entry[] };

const MONTH = new Intl.DateTimeFormat("en-KE", {
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

/** "2026-11-04" as "2026-11", or "undated" when there is no date. */
function monthOf(entry: Entry): string {
  return entry.occurred_on ? entry.occurred_on.slice(0, 7) : "undated";
}

function labelFor(key: string): string {
  if (key === "undated") return "No date";
  const [year, month] = key.split("-").map(Number);
  return MONTH.format(new Date(Date.UTC(year, month - 1, 1)));
}

/** Entries in runs of the same month, keeping their order (newest first from the API). */
export function groupByMonth(entries: Entry[]): MonthGroup[] {
  const groups: MonthGroup[] = [];
  for (const entry of entries) {
    const key = monthOf(entry);
    const last = groups.at(-1);
    if (last?.key === key) last.entries.push(entry);
    else groups.push({ key, label: labelFor(key), entries: [entry] });
  }
  return groups;
}
