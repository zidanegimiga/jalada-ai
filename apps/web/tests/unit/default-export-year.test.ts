import { describe, expect, it } from "vitest";

import { defaultExportYear } from "@/features/export/default-year";
import type { Month } from "@/features/ledger/types";

function month(number: number, outBusinessCents = 0): Month {
  return {
    month: number,
    in_business_cents: 0,
    in_personal_cents: 0,
    out_business_cents: outBusinessCents,
    out_personal_cents: 0,
  };
}

describe("defaultExportYear", () => {
  it("offers last year when it has confirmed money, because that return is being filed", () => {
    const lastYear = [month(1), month(11, 15000), month(12)];

    expect(defaultExportYear(2026, lastYear)).toBe(2025);
  });

  it("offers this year to someone whose records start this year", () => {
    expect(defaultExportYear(2026, [month(1), month(2)])).toBe(2026);
    expect(defaultExportYear(2026, [])).toBe(2026);
  });
});
