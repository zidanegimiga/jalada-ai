/** Dates as "YYYY-MM-DD" strings, worked on in UTC so time zones never move a day. */

export function parseDay(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return null;
  return new Date(
    Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])),
  );
}

export function formatDay(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export function addDays(date: Date, days: number): Date {
  return new Date(date.getTime() + days * 86_400_000);
}

/** Today in the browser's own calendar, as a UTC date. */
export function today(): Date {
  const now = new Date();
  return new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
}

/** The six weeks shown for a month, starting on the Monday on or before the 1st. */
export function weeksOf(year: number, monthIndex: number): Date[] {
  const first = new Date(Date.UTC(year, monthIndex, 1));
  const back = (first.getUTCDay() + 6) % 7;
  const start = addDays(first, -back);
  return Array.from({ length: 42 }, (_, index) => addDays(start, index));
}
