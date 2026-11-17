import type { Month } from "@/features/ledger/types";

/** Whether a month has any confirmed money in or out. */
function hasMoney(month: Month): boolean {
  return (
    month.in_business_cents +
      month.in_personal_cents +
      month.out_business_cents +
      month.out_personal_cents >
    0
  );
}

/**
 * The year the download offers first. Returns are filed for last year, so that is the usual
 * choice; a user whose records start this year gets this year instead.
 */
export function defaultExportYear(
  currentYear: number,
  lastYearMonths: Month[],
): number {
  return lastYearMonths.some(hasMoney) ? currentYear - 1 : currentYear;
}
