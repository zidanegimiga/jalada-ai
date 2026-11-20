import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import {
  contentSecurityPolicy,
  isAllowedRequest,
  isOwnPage,
  mayOpenOutside,
  windowPreferences,
} from "../src/main/security";

const API = "https://api.jalada.example";
const ENTRY = "file:///Applications/Jalada.app/renderer/index.html";

describe("window settings", () => {
  it("give the page no Node.js and run it sandboxed behind the bridge", () => {
    expect(windowPreferences("/preload.cjs")).toMatchObject({
      preload: "/preload.cjs",
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
      webviewTag: false,
      webSecurity: true,
    });
  });
});

describe("outgoing requests", () => {
  it("allow the app's own files and the API", () => {
    expect(isAllowedRequest(ENTRY, API)).toBe(true);
    expect(isAllowedRequest(`${API}/v1/entries`, API)).toBe(true);
  });

  it("block every other server, including look-alikes of the API", () => {
    for (const address of [
      "https://fonts.googleapis.com/css2?family=Onest",
      "https://www.google-analytics.com/collect",
      "http://api.jalada.example/v1/entries",
      "https://api.jalada.example.evil.example/v1",
      "https://api.jalada.example:8443/v1",
      "not an address",
    ]) {
      expect(isAllowedRequest(address, API), address).toBe(false);
    }
  });
});

describe("navigation", () => {
  it("keeps windows on the app's own page", () => {
    expect(isOwnPage(`${ENTRY}#ledger`, ENTRY)).toBe(true);
    expect(isOwnPage("file:///etc/passwd", ENTRY)).toBe(false);
    expect(isOwnPage("https://jalada.example", ENTRY)).toBe(false);
  });

  it("only hands the web app's own pages to the system browser", () => {
    const web = "https://jalada.example";
    expect(mayOpenOutside("https://jalada.example/privacy", web)).toBe(true);
    for (const address of [
      "https://example.com",
      "https://jalada.example.evil.example/privacy",
      "http://jalada.example/privacy",
      "file:///etc/passwd",
      "smb://share/run.exe",
      "javascript:alert(1)",
    ]) {
      expect(mayOpenOutside(address, web), address).toBe(false);
    }
  });
});

describe("content security policy", () => {
  it("lets the page load only its own code and reach no server itself", () => {
    const policy = contentSecurityPolicy();

    expect(policy).toContain("default-src 'none'");
    expect(policy).toContain("script-src 'self'");
    expect(policy).toContain("connect-src 'none'");
    expect(policy).not.toContain("unsafe");
  });

  it("is the same in the page, which gets no headers when loaded from a file", () => {
    const page = readFileSync(
      join(__dirname, "../src/renderer/index.html"),
      "utf8",
    );
    const inPage =
      /http-equiv="Content-Security-Policy"\s+content="([^"]+)"/.exec(
        page,
      )?.[1];

    expect(inPage).toBe(contentSecurityPolicy());
  });
});
