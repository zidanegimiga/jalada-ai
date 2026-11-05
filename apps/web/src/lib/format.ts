const shillings = new Intl.NumberFormat("en-KE", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const day = new Intl.DateTimeFormat("en-KE", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

/** 125000 cents as "KSh 1,250.00". Amounts stay whole cents until they are shown. */
export function formatKsh(cents: number): string {
  return `KSh ${shillings.format(cents / 100)}`;
}

/** Cents as the plain text the API expects back, such as "1250.00". */
export function centsToInput(cents: number): string {
  return (cents / 100).toFixed(2);
}

/** "2026-11-04" as "4 Nov 2026", read as a calendar date with no time zone shift. */
export function formatDay(isoDate: string): string {
  const [year, month, date] = isoDate.split("-").map(Number);
  return day.format(new Date(Date.UTC(year, month - 1, date)));
}
