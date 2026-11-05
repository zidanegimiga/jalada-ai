import type { Entry } from "@/features/review/types";

export type LedgerPage = { items: Entry[]; next_cursor: string | null };

export type Month = {
  month: number;
  in_business_cents: number;
  in_personal_cents: number;
  out_business_cents: number;
  out_personal_cents: number;
};

export type LedgerQuery = {
  month?: string;
  direction?: string;
  purpose?: string;
  cursor?: string;
};
