import { describe, expect, it } from "vitest";

import { safeReturnPath } from "@/shared/config/return-path";

describe("return path after sign-in", () => {
  it("keeps a page of this site, with its query", () => {
    expect(safeReturnPath("/ledger")).toBe("/ledger");
    expect(safeReturnPath("/desktop/sign-in?state=abc")).toBe(
      "/desktop/sign-in?state=abc",
    );
  });

  it("sends anything else home", () => {
    for (const unsafe of [
      null,
      "",
      "ledger",
      "//evil.example/steal",
      "/\\evil.example",
      "https://evil.example",
      "javascript:alert(1)",
    ]) {
      expect(safeReturnPath(unsafe), String(unsafe)).toBe("/");
    }
  });
});
