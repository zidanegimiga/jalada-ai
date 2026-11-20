import { existsSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import manifest from "@/app/manifest";

const PUBLIC = join(__dirname, "../../public");

describe("web app manifest", () => {
  const app = manifest();

  it("opens as its own window at home", () => {
    expect(app).toMatchObject({
      name: "Jalada AI",
      start_url: "/",
      display: "standalone",
    });
  });

  it("has ordinary and maskable icons at both sizes Android asks for", () => {
    for (const size of ["192x192", "512x512"]) {
      for (const purpose of ["any", "maskable"]) {
        expect(app.icons).toContainEqual(
          expect.objectContaining({ sizes: size, purpose }),
        );
      }
    }
  });

  it("points only at icons that exist", () => {
    for (const icon of app.icons ?? []) {
      expect(existsSync(join(PUBLIC, icon.src))).toBe(true);
    }
  });
});
