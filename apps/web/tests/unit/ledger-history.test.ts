import { describe, expect, it } from "vitest";

import { describeEvent, describeEvidence } from "@/features/ledger/history";
import type { HistoryItem } from "@/features/ledger/types";

const item = (overrides: Partial<HistoryItem>): HistoryItem => ({
  at: "2026-11-17T09:00:00Z",
  actor: "user",
  action: "confirmed",
  changed: [],
  ...overrides,
});

describe("describeEvent", () => {
  it("names who did it, with Jalada AI for the pipeline", () => {
    expect(
      describeEvent(item({ actor: "pipeline", action: "proposed" })),
    ).toEqual({
      title: "Read by Jalada AI",
    });
    expect(describeEvent(item({})).title).toBe("Confirmed by you");
  });

  it("says what a change touched", () => {
    expect(
      describeEvent(
        item({ action: "corrected", changed: ["amount", "date", "category"] }),
      ),
    ).toEqual({
      title: "Changed by you",
      detail: "Changed the amount, the date and the category",
    });
  });
});

describe("describeEvidence", () => {
  it("names the evidence and how it came to be linked", () => {
    expect(
      describeEvidence({
        id: "e",
        role: "receipt",
        linked_by: "suggested",
        linked_at: "2026-11-17T09:00:00Z",
        content_type: "image/jpeg",
        received_at: "2026-11-17T09:00:00Z",
      }),
    ).toEqual({ title: "Receipt", detail: "A match you accepted" });
  });
});
