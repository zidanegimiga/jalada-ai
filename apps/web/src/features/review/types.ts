import type { Schema } from "@/lib/api-schema";

export type Category = Schema<"CategoryResponse">;

export type Entry = Schema<"EntryResponse">;

export type ReviewItem = Schema<"ReviewItemResponse">;

/** What the entry form sends. The amount is text such as "1250.00", never a number. */
export type EntryValues = {
  occurred_on: string;
  amount: string;
  direction: "in" | "out";
  counterparty: string;
  category: string;
};
