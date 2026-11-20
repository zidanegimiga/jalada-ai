import { describe, expect, it } from "vitest";

import { loadConfig } from "../src/main/config";

describe("desktop config", () => {
  it("uses the live API in a packaged build when nothing is set", () => {
    expect(loadConfig({}, false).apiOrigin).toBe(
      "https://jalada-api.onrender.com",
    );
  });

  it("keeps only the origin of the address given", () => {
    expect(
      loadConfig({ JALADA_API_URL: "https://api.example/v1/" }).apiOrigin,
    ).toBe("https://api.example");
  });

  it("allows plain http only on this computer", () => {
    expect(
      loadConfig({ JALADA_API_URL: "http://localhost:8000" }).apiOrigin,
    ).toBe("http://localhost:8000");
    expect(() => loadConfig({ JALADA_API_URL: "http://api.example" })).toThrow(
      /https/,
    );
  });

  it("refuses something that is not an address", () => {
    expect(() => loadConfig({ JALADA_API_URL: "api.example" })).toThrow(
      /not an address/,
    );
  });

  it("uses the live web app in a packaged build when nothing is set", () => {
    expect(loadConfig({}, false).webOrigin).toBe(
      "https://jalada-ai.netlify.app",
    );
  });

  it("holds the web app address to the same https rule", () => {
    expect(() =>
      loadConfig({ JALADA_WEB_URL: "http://jalada.example" }),
    ).toThrow(/JALADA_WEB_URL must use https/);
  });

  it("uses the local stack when run from source, so changes are tried locally", () => {
    expect(loadConfig({}, true)).toEqual({
      apiOrigin: "http://localhost:8000",
      webOrigin: "http://localhost:3000",
    });
  });

  it("lets the addresses be set either way", () => {
    expect(
      loadConfig({ JALADA_WEB_URL: "https://jalada.example" }, true).webOrigin,
    ).toBe("https://jalada.example");
  });
});
