import type { Category, Entry, ReviewItem } from "../types";

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
    ...overrides,
  };
}

export function item(entryValue: Entry | null): ReviewItem {
  return {
    entry: entryValue,
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
