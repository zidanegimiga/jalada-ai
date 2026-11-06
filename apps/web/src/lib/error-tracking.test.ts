import type { ErrorEvent } from "@sentry/nextjs";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  errorTrackingOptions,
  scrubEvent,
  withoutQuery,
} from "./error-tracking";

afterEach(() => vi.unstubAllEnvs());

describe("error tracking", () => {
  it("cuts query strings and fragments off addresses", () => {
    expect(withoutQuery("https://x.example/ledger?month=2026-03#top")).toBe(
      "https://x.example/ledger",
    );
    expect(withoutQuery("/review")).toBe("/review");
  });

  it("removes the user, request details and queries in breadcrumbs", () => {
    const event = scrubEvent({
      type: undefined,
      user: { id: "1", email: "jane@example.com" },
      request: {
        method: "GET",
        url: "https://jalada.example/ledger?month=2026-03",
        cookies: { jalada_session: "secret" },
        headers: { Cookie: "jalada_session=secret" },
        query_string: "month=2026-03",
      },
      breadcrumbs: [
        {
          category: "fetch",
          data: { url: "/v1/entries?from=2026-03-01", method: "GET" },
        },
        {
          category: "navigation",
          data: { from: "/ledger?a=1", to: "/review?b=2" },
        },
      ],
    } as ErrorEvent);

    expect(event.user).toBeUndefined();
    expect(event.request).toEqual({
      method: "GET",
      url: "https://jalada.example/ledger",
    });
    expect(event.breadcrumbs?.[0].data).toEqual({
      url: "/v1/entries",
      method: "GET",
    });
    expect(event.breadcrumbs?.[1].data).toEqual({
      from: "/ledger",
      to: "/review",
    });
  });

  it("is off until a DSN is set at build time, and collects nothing personal", () => {
    vi.stubEnv("NEXT_PUBLIC_SENTRY_DSN", "");
    expect(errorTrackingOptions().enabled).toBe(false);

    vi.stubEnv("NEXT_PUBLIC_SENTRY_DSN", "https://key@errors.example.com/1");
    const options = errorTrackingOptions();
    expect(options.enabled).toBe(true);
    expect(options.tracesSampleRate).toBe(0);
    expect(
      options.beforeBreadcrumb?.({ category: "console", message: "x" }),
    ).toBeNull();
    expect(
      options.beforeBreadcrumb?.({ category: "navigation", data: {} }),
    ).toEqual({ category: "navigation", data: {} });
    expect(options.dataCollection).toMatchObject({
      userInfo: false,
      cookies: false,
      httpHeaders: false,
      httpBodies: [],
      urlQueryParams: false,
    });
  });
});
