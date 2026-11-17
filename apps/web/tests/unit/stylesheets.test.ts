import { readdirSync, readFileSync } from "node:fs";
import { basename, dirname, join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const SRC = join(__dirname, "../../src");

function files(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((item) => {
    const path = join(folder, item.name);
    return item.isDirectory() ? files(path) : [path];
  });
}

const all = files(SRC);
const IMPORT = /^import\s+["'](\.[^"']+)["'];?$/gm;

/** Every file a side-effect import such as `import "./Splash.css"` points at. */
function sideEffectImports(): Set<string> {
  const found = new Set<string>();
  for (const path of all.filter((p) => /\.tsx?$/.test(p))) {
    for (const match of readFileSync(path, "utf8").matchAll(IMPORT)) {
      found.add(resolve(dirname(path), match[1]));
    }
  }
  return found;
}

describe("stylesheets", () => {
  it("are each imported by name", () => {
    const imported = sideEffectImports();
    const missing = all
      .filter((path) => path.endsWith(".css"))
      .filter((path) => !imported.has(path))
      .map((path) => relative(SRC, path));

    expect(missing).toEqual([]);
  });

  it("are the only side-effect imports, so none is mistaken for a module", () => {
    const strays = [...sideEffectImports()]
      .filter((path) => !path.endsWith(".css"))
      .map((path) => basename(path));

    expect(strays).toEqual([]);
  });
});
