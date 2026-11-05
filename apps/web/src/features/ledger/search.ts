import type { LedgerQuery } from "./types";

/** Turns the page's own filters (a month such as "2026-11") into the API's query. */
export function ledgerSearch(query: LedgerQuery): URLSearchParams {
  const search = new URLSearchParams();
  if (query.month && /^\d{4}-\d{2}$/.test(query.month)) {
    const [year, month] = query.month.split("-").map(Number);
    const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate();
    search.set("from", `${query.month}-01`);
    search.set("to", `${query.month}-${String(lastDay).padStart(2, "0")}`);
  }
  for (const key of ["direction", "purpose", "cursor"] as const) {
    if (query[key]) search.set(key, query[key]);
  }
  return search;
}
