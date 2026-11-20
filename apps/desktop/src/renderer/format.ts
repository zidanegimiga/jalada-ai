import type { LocalEntry } from "@shared/records";

const SHILLINGS = new Intl.NumberFormat("en-KE", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const DAY = new Intl.DateTimeFormat("en-KE", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "Africa/Nairobi",
});

const TIME = new Intl.DateTimeFormat("en-KE", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "Africa/Nairobi",
});

/** "+KSh 35,000.00" for money in, "−KSh 2,450.00" for money out. */
export function signedAmount(
  entry: Pick<LocalEntry, "amountCents" | "direction">,
): string {
  if (entry.amountCents === null) return "No amount";
  const sign =
    entry.direction === "in" ? "+" : entry.direction === "out" ? "−" : "";
  return `${sign}KSh ${SHILLINGS.format(entry.amountCents / 100)}`;
}

/** "17 Nov 2026" from "2026-11-17", read as a calendar day, not a moment in time. */
export function day(occurredOn: string | null): string {
  if (!occurredOn) return "No date";
  const [year, month, date] = occurredOn.split("-").map(Number);
  if (!year || !month || !date) return "No date";
  return DAY.format(new Date(Date.UTC(year, month - 1, date, 9)));
}

/** When the copy here was last refreshed, in Nairobi time, or that it never was. */
export function updatedLine(updatedAt: string | null): string {
  if (!updatedAt) return "Not copied from the server yet";
  return `Updated ${TIME.format(new Date(updatedAt))}`;
}

/** "20 Nov, 09:15" in Nairobi time, for when a change was made here. */
export function moment(at: string): string {
  return TIME.format(new Date(at));
}
