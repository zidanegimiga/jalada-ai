import type { EvidenceItem } from "@/features/evidence/api";

export type Category = {
  slug: string;
  name: string;
  direction: "in" | "out";
  purpose: string;
};

export type Entry = {
  id: string;
  evidence_id: string;
  status: string;
  occurred_on: string | null;
  direction: "in" | "out" | null;
  amount_cents: number | null;
  counterparty: string | null;
  purpose: string;
  category: string | null;
  category_name: string | null;
  kind?: "transaction" | "withholding_certificate";
  tax_withheld_cents?: number | null;
  certificate_serial?: string | null;
  // In the ledger: the certificate a payment was linked to, or a certificate's payments.
  linked_certificate_id?: string | null;
  linked_payment_ids?: string[];
};

export type ReviewItem = { evidence: EvidenceItem; entry: Entry | null };

/** What the entry form sends. The amount is text such as "1250.00", never a number. */
export type EntryValues = {
  occurred_on: string;
  amount: string;
  direction: "in" | "out";
  counterparty: string;
  category: string;
};
