import type { CategoryTotal, Month } from "./types";

/** One month's money in and out, as the charts draw it. */
export type MonthPoint = {
  key: string;
  label: string;
  short: string;
  inCents: number;
  outCents: number;
  /** The business part of each; the rest is personal. */
  inBusinessCents: number;
  outBusinessCents: number;
};

const LONG = new Intl.DateTimeFormat("en-KE", {
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});
const SHORT = new Intl.DateTimeFormat("en-KE", {
  month: "short",
  timeZone: "UTC",
});

function point(
  year: number,
  month: Month | undefined,
  index: number,
): MonthPoint {
  const date = new Date(Date.UTC(year, index, 1));
  return {
    key: `${year}-${String(index + 1).padStart(2, "0")}`,
    label: LONG.format(date),
    short: SHORT.format(date),
    inCents: month ? month.in_business_cents + month.in_personal_cents : 0,
    outCents: month ? month.out_business_cents + month.out_personal_cents : 0,
    inBusinessCents: month?.in_business_cents ?? 0,
    outBusinessCents: month?.out_business_cents ?? 0,
  };
}

/** The twelve months of one year, January first. */
export function yearPoints(year: number, months: Month[]): MonthPoint[] {
  return Array.from({ length: 12 }, (_, index) =>
    point(year, months[index], index),
  );
}

/** The last `count` months up to and including this one, which may reach into last year. */
export function recentPoints(
  year: number,
  month: number,
  thisYear: Month[],
  lastYear: Month[],
  count = 6,
): MonthPoint[] {
  return Array.from({ length: count }, (_, step) => {
    const index = month - count + step;
    return index >= 0
      ? point(year, thisYear[index], index)
      : point(year - 1, lastYear[index + 12], index + 12);
  });
}

export type CategorySlice = { name: string; cents: number };

/** The biggest categories in one direction, with the rest gathered as "Everything else". */
export function topCategories(
  totals: CategoryTotal[],
  direction: "in" | "out",
  limit = 5,
): CategorySlice[] {
  const mine = totals
    .filter((total) => total.direction === direction)
    .map(({ name, cents }) => ({ name, cents }));
  if (mine.length <= limit + 1) return mine;
  const rest = mine.slice(limit).reduce((sum, slice) => sum + slice.cents, 0);
  return [...mine.slice(0, limit), { name: "Everything else", cents: rest }];
}
