import { describe, expect, it } from "vitest";

import { loadConfig } from "../src/main/config";

describe("desktop config", () => {
  it("uses the live API when nothing is set", () => {
    expect(loadConfig({}).apiOrigin).toBe("https://jalada-api.onrender.com");
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
});
