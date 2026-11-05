import { describe, expect, it } from "vitest";

import { ledgerSearch } from "./search";

describe("ledgerSearch", () => {
  it("turns a month into its first and last day", () => {
    expect(ledgerSearch({ month: "2026-02" }).toString()).toBe(
      "from=2026-02-01&to=2026-02-28",
    );
    expect(ledgerSearch({ month: "2028-02" }).get("to")).toBe("2028-02-29");
  });

  it("passes the other filters through and ignores a malformed month", () => {
    const search = ledgerSearch({
      month: "Feb",
      direction: "in",
      purpose: "business",
      cursor: "abc",
    });

    expect(search.toString()).toBe("direction=in&purpose=business&cursor=abc");
  });
});
