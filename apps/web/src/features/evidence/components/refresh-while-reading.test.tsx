import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GIVE_UP_AFTER_MS, RefreshWhileReading } from "./refresh-while-reading";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

function answer(...statuses: string[]) {
  const fetch = vi.fn();
  for (const status of statuses)
    fetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ id: "e1", status })),
    );
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

beforeEach(() => {
  vi.useFakeTimers();
  router.refresh.mockReset();
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("RefreshWhileReading", () => {
  it("refreshes the page once the worker has finished", async () => {
    const fetch = answer("processing", "needs_review");
    render(<RefreshWhileReading waiting={["e1"]} />);

    await act(() => vi.advanceTimersByTimeAsync(2_000));
    expect(fetch).toHaveBeenCalledWith("/v1/evidence/e1");
    expect(router.refresh).not.toHaveBeenCalled();

    await act(() => vi.advanceTimersByTimeAsync(2_000));
    expect(router.refresh).toHaveBeenCalledTimes(1);
  });

  it("does nothing when nothing is being read", async () => {
    const fetch = answer();
    render(<RefreshWhileReading waiting={[]} />);

    await act(() => vi.advanceTimersByTimeAsync(GIVE_UP_AFTER_MS));
    expect(fetch).not.toHaveBeenCalled();
  });

  it("gives up after two minutes", async () => {
    const fetch = vi.fn(
      async () =>
        new Response(JSON.stringify({ id: "e1", status: "processing" })),
    );
    vi.stubGlobal("fetch", fetch);
    render(<RefreshWhileReading waiting={["e1"]} />);

    await act(() => vi.advanceTimersByTimeAsync(GIVE_UP_AFTER_MS));
    const checks = fetch.mock.calls.length;
    await act(() => vi.advanceTimersByTimeAsync(60_000));

    expect(fetch.mock.calls.length).toBe(checks);
    expect(checks).toBeGreaterThan(5);
    expect(router.refresh).not.toHaveBeenCalled();
  });
});
