import { describe, expect, it } from "vitest";

import { groupByMonth } from "@/features/ledger/group";

import { entry } from "../support/review-fixtures";

describe("groupByMonth", () => {
  it("puts entries in runs of the same month, keeping their order", () => {
    const groups = groupByMonth([
      entry({ id: "a", occurred_on: "2026-11-14" }),
      entry({ id: "b", occurred_on: "2026-11-02" }),
      entry({ id: "c", occurred_on: "2026-10-30" }),
    ]);

    expect(groups.map((group) => group.label)).toEqual([
      "November 2026",
      "October 2026",
    ]);
    expect(groups[0].entries.map((e) => e.id)).toEqual(["a", "b"]);
  });

  it("names entries without a date", () => {
    const [group] = groupByMonth([
      entry({ id: "a", occurred_on: null as unknown as string }),
    ]);

    expect(group.label).toBe("No date");
  });
});
