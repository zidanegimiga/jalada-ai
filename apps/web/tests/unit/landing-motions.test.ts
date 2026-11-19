import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { MOTIONS } from "@/features/landing/motion";

const COMPONENTS = join(__dirname, "../../src/features/landing/components");

/** Every effect name the landing page's markup asks for in data-motion. */
function namesInMarkup(): string[] {
  return readdirSync(COMPONENTS, { recursive: true, encoding: "utf8" })
    .filter((path) => path.endsWith(".tsx"))
    .flatMap((path) => {
      const source = readFileSync(join(COMPONENTS, path), "utf8");
      return [...source.matchAll(/data-motion="([^"]+)"/g)].flatMap((match) =>
        match[1].split(" "),
      );
    });
}

describe("landing motions", () => {
  it("has an effect for every name the markup uses", () => {
    const unknown = namesInMarkup().filter((name) => !(name in MOTIONS));

    expect(unknown).toEqual([]);
  });

  it("has no effect the markup never uses", () => {
    const used = new Set(namesInMarkup());

    expect(Object.keys(MOTIONS).filter((name) => !used.has(name))).toEqual([]);
  });
});
