import type { Entry } from "@/features/review/types";

export type Certificate = {
  certificate: Entry;
  /** Gross minus tax withheld: what the client would have paid in. */
  expected_payment_cents: number;
  linked_cents: number;
  payments: Entry[];
  suggestions: Entry[];
};
