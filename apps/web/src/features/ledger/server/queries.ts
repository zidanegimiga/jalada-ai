import "server-only";

import { apiGet } from "@/shared/api/server-api";

import { ledgerSearch } from "../search";
import type { CategoryTotal, LedgerPage, LedgerQuery, Month } from "../types";

export async function getLedger(query: LedgerQuery): Promise<LedgerPage> {
  const page = await apiGet<LedgerPage>(`/v1/entries?${ledgerSearch(query)}`);
  return page ?? { items: [], next_cursor: null };
}

/** Totals for each month of a year, January first. Empty when the API cannot be reached. */
export async function getYear(year: number): Promise<Month[]> {
  const summary = await apiGet<{ months: Month[] }>(
    `/v1/summary/monthly?year=${year}`,
  );
  return summary?.months ?? [];
}

/** Confirmed money per category between two "YYYY-MM-DD" dates, largest first. */
export async function getCategoryTotals(
  from: string,
  to: string,
): Promise<CategoryTotal[]> {
  const params = new URLSearchParams({ from, to });
  const found = await apiGet<{ totals: CategoryTotal[] }>(
    `/v1/summary/categories?${params}`,
  );
  return found?.totals ?? [];
}

export async function getMonth(
  year: number,
  month: number,
): Promise<Month | null> {
  return (await getYear(year))[month - 1] ?? null;
}
