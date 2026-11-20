import { describe, expect, it } from "vitest";

import { day, signedAmount, updatedLine } from "../src/renderer/format";

describe("formatting the ledger", () => {
  it("signs amounts by direction", () => {
    expect(signedAmount({ amountCents: 3_500_000, direction: "in" })).toBe(
      "+KSh 35,000.00",
    );
    expect(signedAmount({ amountCents: 245_000, direction: "out" })).toBe(
      "−KSh 2,450.00",
    );
    expect(signedAmount({ amountCents: null, direction: "out" })).toBe(
      "No amount",
    );
  });

  it("shows a calendar day the same in every timezone", () => {
    expect(day("2026-11-17")).toBe("17 Nov 2026");
    expect(day(null)).toBe("No date");
    expect(day("not a date")).toBe("No date");
  });

  it("says when the copy here was last refreshed, in Nairobi time", () => {
    expect(updatedLine(null)).toBe("Not copied from the server yet");
    expect(updatedLine("2026-11-20T09:00:00Z")).toBe("Updated 20 Nov, 12:00");
  });
});
