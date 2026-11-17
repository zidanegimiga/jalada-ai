import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";

// Raw sizes that have a token in globals.css. Screens use the token, so the scale stays
// the same everywhere.
const RAW = [
  /\btext-(xs|sm|base|lg|xl|[2-9]xl)\b/,
  /\brounded-(sm|md|lg|xl|[2-4]xl)\b/,
  /\bmax-w-(sm|md|lg|xl)\b/,
];

function sources(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((item) => {
    const path = join(folder, item.name);
    if (item.isDirectory()) return sources(path);
    return /\.tsx$/.test(item.name) && !item.name.includes(".test.")
      ? [path]
      : [];
  });
}

describe("design tokens", () => {
  it("are used instead of raw sizes and radii", () => {
    const root = join(__dirname, "../../src");
    const found = sources(root).flatMap((path) =>
      RAW.flatMap((pattern) => {
        const match = readFileSync(path, "utf8").match(pattern);
        return match ? [`${relative(root, path)}: ${match[0]}`] : [];
      }),
    );

    expect(found).toEqual([]);
  });
});
