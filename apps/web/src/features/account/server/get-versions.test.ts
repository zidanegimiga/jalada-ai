import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

const { shortVersion } = await import("./get-versions");

describe("shortVersion", () => {
  it("shortens a full commit hash and leaves anything else alone", () => {
    expect(shortVersion("a".repeat(40))).toBe("aaaaaaa");
    expect(shortVersion("development")).toBe("development");
    expect(shortVersion("1.2.0")).toBe("1.2.0");
  });
});
