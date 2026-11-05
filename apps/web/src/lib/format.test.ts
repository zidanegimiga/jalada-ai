import { describe, expect, it } from "vitest";

import { centsToInput, formatDay, formatKsh } from "./format";

describe("format", () => {
  it("shows cents as shillings", () => {
    expect(formatKsh(125000)).toBe("KSh 1,250.00");
    expect(formatKsh(5)).toBe("KSh 0.05");
  });

  it("turns cents back into the text the API reads", () => {
    expect(centsToInput(125000)).toBe("1250.00");
  });

  it("shows calendar dates without shifting the day", () => {
    expect(formatDay("2026-11-04")).toBe("4 Nov 2026");
  });
});
