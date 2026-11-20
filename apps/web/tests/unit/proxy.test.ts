// @vitest-environment node
import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { proxy } from "@/proxy";
import { SESSION_COOKIE } from "@/shared/config/session-cookie";

function visit(path: string, signedIn = false) {
  const headers = signedIn ? { cookie: `${SESSION_COOKIE}=x` } : undefined;
  return proxy(new NextRequest(`http://localhost${path}`, { headers }));
}

describe("proxy", () => {
  it("shows signed-out visitors the landing page at the front door", () => {
    const response = visit("/");

    expect(response.headers.get("x-middleware-rewrite")).toBe(
      "http://localhost/welcome",
    );
  });

  it("shows signed-in people their home page at the front door", () => {
    const response = visit("/", true);

    expect(response.headers.get("x-middleware-rewrite")).toBeNull();
    expect(response.headers.get("location")).toBeNull();
  });

  it("sends signed-out visitors to sign in from any other page", () => {
    expect(visit("/ledger").headers.get("location")).toBe(
      "http://localhost/signin",
    );
  });

  it("lets anyone open the landing page and the privacy notice", () => {
    for (const path of ["/welcome", "/privacy", "/offline"]) {
      expect(visit(path).headers.get("location")).toBeNull();
    }
  });
});
