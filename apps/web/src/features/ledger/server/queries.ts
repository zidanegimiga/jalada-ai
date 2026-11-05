import "server-only";

import { apiGet } from "@/lib/server-api";

import { ledgerSearch } from "../search";
import type { LedgerPage, LedgerQuery, Month } from "../types";

export async function getLedger(query: LedgerQuery): Promise<LedgerPage> {
  const page = await apiGet<LedgerPage>(`/v1/entries?${ledgerSearch(query)}`);
  return page ?? { items: [], next_cursor: null };
}

export async function getMonth(
  year: number,
  month: number,
): Promise<Month | null> {
  const summary = await apiGet<{ months: Month[] }>(
    `/v1/summary/monthly?year=${year}`,
  );
  return summary?.months[month - 1] ?? null;
}
