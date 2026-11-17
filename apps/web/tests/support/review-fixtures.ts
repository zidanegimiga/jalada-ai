import type { Category, Entry, ReviewItem } from "@/features/review/types";

export const CATEGORIES: Category[] = [
  {
    slug: "personal_food",
    name: "Food",
    direction: "out",
    purpose: "personal",
  },
  {
    slug: "business_stock",
    name: "Stock and supplies",
    direction: "out",
    purpose: "business",
  },
  { slug: "salary", name: "Salary", direction: "in", purpose: "personal" },
];

export function entry(overrides: Partial<Entry> = {}): Entry {
  return {
    id: "entry-1",
    evidence_id: "evidence-1",
    kind: "transaction",
    status: "proposed",
    reference: null,
    mpesa_code: null,
    certificate_serial: null,
    tax_withheld_cents: null,
    payer_tax_number: null,
    confidence: 1,
    occurred_on: "2026-11-04",
    direction: "out",
    amount_cents: 15000,
    counterparty: "JANE WANJIKU",
    purpose: "personal",
    category: "personal_food",
    category_name: "Food",
    category_suggested: false,
    ...overrides,
  };
}

export function item(entryValue: Entry | null): ReviewItem {
  return {
    entry: entryValue,
    ask_how_paid: false,
    ready: false,
    ask_own_account: false,
    evidence: {
      id: "evidence-1",
      source: "web_paste",
      kind: "mpesa_message",
      status: "proposed",
      content_type: "text/plain",
      size_bytes: 10,
      received_at: "2026-11-04T10:00:00Z",
      duplicate: false,
    },
  };
}

/** A paybill payment, and a receipt that may be the same purchase. */
export function matchItem(): ReviewItem {
  const payment = entry({
    amount_cents: 41900,
    counterparty: "M-PESA CARD",
    occurred_on: "2026-11-05",
  });
  return {
    ...item(payment),
    match: {
      suggestion_id: "suggestion-1",
      receipt: {
        ...item(null).evidence,
        id: "receipt-1",
        kind: "receipt",
        status: "candidate",
        content_type: "image/jpeg",
      },
      occurred_on: "2026-11-05",
      amount_cents: 41900,
      counterparty: "SAMPLE MUSIC SHOP",
      reasons: ["same amount", "same day"],
    },
  };
}

/** A receipt whose payment never arrived, asked about on To check. */
export function receiptItem(): ReviewItem {
  const receipt = item(
    entry({
      id: "candidate-1",
      evidence_id: "receipt-1",
      status: "needs_review",
      amount_cents: 41900,
      counterparty: "SAMPLE MUSIC SHOP",
      occurred_on: "2026-11-05",
    }),
  );
  return {
    ...receipt,
    ask_how_paid: true,
    evidence: {
      ...receipt.evidence,
      id: "receipt-1",
      kind: "receipt",
      status: "candidate",
      content_type: "image/jpeg",
    },
  };
}
