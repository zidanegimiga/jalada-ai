import type { Schema } from "@/lib/api-schema";

export type LedgerPage = Schema<"LedgerResponse">;

export type Month = Schema<"MonthResponse">;

export type LedgerQuery = {
  month?: string;
  direction?: string;
  purpose?: string;
  cursor?: string;
};
