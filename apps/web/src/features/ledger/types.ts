import type { Schema } from "@/shared/api/api-schema";

export type LedgerPage = Schema<"LedgerResponse">;

export type Month = Schema<"MonthResponse">;

export type LedgerQuery = {
  month?: string;
  direction?: string;
  purpose?: string;
  /** Words to find in who the money was with. */
  q?: string;
  cursor?: string;
};

export type CategoryTotal = Schema<"CategoryTotalResponse">;
