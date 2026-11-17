import { describe, expect, it } from "vitest";

import { recentPoints, topCategories } from "@/features/ledger/charts";
import type { CategoryTotal, Month } from "@/features/ledger/types";

function month(number: number, inCents = 0, outCents = 0): Month {
  return {
    month: number,
    in_business_cents: inCents,
    in_personal_cents: 0,
    out_business_cents: 0,
    out_personal_cents: outCents,
  };
}

const twelve = (fill: (n: number) => Month) =>
  Array.from({ length: 12 }, (_, i) => fill(i + 1));

describe("recentPoints", () => {
  it("reaches back into last year for the first months of a year", () => {
    const thisYear = twelve((n) => month(n, n * 100));
    const lastYear = twelve((n) => month(n, 0, n * 10));

    const points = recentPoints(2026, 2, thisYear, lastYear);

    expect(points.map((p) => p.key)).toEqual([
      "2025-09",
      "2025-10",
      "2025-11",
      "2025-12",
      "2026-01",
      "2026-02",
    ]);
    expect(points[0].outCents).toBe(90);
    expect(points[5]).toMatchObject({ label: "February 2026", inCents: 200 });
  });
});

describe("topCategories", () => {
  const total = (
    name: string,
    cents: number,
    direction: "in" | "out" = "out",
  ) => ({ name, cents, direction, category: name }) as CategoryTotal;

  it("keeps one direction and gathers the smallest as everything else", () => {
    const totals = [
      total("Salary", 900, "in"),
      ...["A", "B", "C", "D", "E", "F", "G"].map((name, i) =>
        total(name, 700 - i * 100),
      ),
    ];

    const out = topCategories(totals, "out");

    expect(out.map((s) => s.name)).toEqual([
      "A",
      "B",
      "C",
      "D",
      "E",
      "Everything else",
    ]);
    expect(out.at(-1)?.cents).toBe(200 + 100);
    expect(topCategories(totals, "in")).toEqual([
      { name: "Salary", cents: 900 },
    ]);
  });
});
