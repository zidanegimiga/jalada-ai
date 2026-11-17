import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { cn, TOKENS } from "@/shared/styles/cn";

describe("cn", () => {
  it("keeps a text colour next to a text size token", () => {
    expect(cn("text-primary-foreground", "text-lead")).toBe(
      "text-primary-foreground text-lead",
    );
  });

  it("lets a later token win over an earlier one of the same scale", () => {
    expect(cn("text-body rounded-card", "text-small rounded-control")).toBe(
      "text-small rounded-control",
    );
  });

  it("knows every token in globals.css", () => {
    const css = readFileSync(
      join(__dirname, "../../src/app/globals.css"),
      "utf8",
    );
    const defined = (scale: string) =>
      [...css.matchAll(new RegExp(`--${scale}-([a-z-]+?):`, "g"))]
        .map((match) => match[1])
        .filter((name) => !name.includes("--"));
    expect(
      defined("text").filter((n) => !/-(line|font|letter)/.test(n)),
    ).toEqual(TOKENS.text);
    expect(
      defined("radius").filter((n) => !/^(sm|md|lg|[2-4]?xl)$/.test(n)),
    ).toEqual(TOKENS.radius);
    expect(defined("spacing")).toEqual(TOKENS.spacing);
    expect(defined("container")).toEqual(TOKENS.container);
    expect(defined("shadow")).toEqual(TOKENS.shadow);
  });
});
