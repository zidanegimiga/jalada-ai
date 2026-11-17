import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import DesignPage from "@/app/(app)/design/page";
import {
  COLOURS,
  ICONS,
  RADII,
  SHADOWS,
  SPACING,
  TYPE,
} from "@/app/(app)/design/tokens";

const css = readFileSync(join(__dirname, "../../src/app/globals.css"), "utf8");

describe("design page", () => {
  it("shows every type step and the components", () => {
    render(<DesignPage />);

    for (const step of TYPE) {
      expect(screen.getByText(`text-${step.name}`)).toBeInTheDocument();
    }
    expect(screen.getByRole("button", { name: "Confirm" })).toBeInTheDocument();
    expect(screen.getByLabelText("Amount")).toBeInTheDocument();
  });

  it("lists only tokens that globals.css defines", () => {
    const names = [
      ...COLOURS.map((name) => `--${name}:`),
      ...TYPE.map(({ name }) => `--text-${name}:`),
      ...RADII.map(({ name }) => `--radius-${name}:`),
      ...[...SPACING, ...ICONS].map(({ name }) => `--spacing-${name}:`),
      ...SHADOWS.map(({ name }) => `--shadow-${name}:`),
    ];

    expect(names.filter((name) => !css.includes(name))).toEqual([]);
  });
});
