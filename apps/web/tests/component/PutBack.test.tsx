import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { PutBack } from "@/features/evidence/components/PutBack";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

function respond(status: number, body: unknown) {
  const text = status === 204 ? null : JSON.stringify(body);
  const fetch = vi.fn().mockResolvedValue(new Response(text, { status }));
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("PutBack", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("takes back Not a transaction and refreshes the page", async () => {
    const fetch = respond(204, null);
    render(<PutBack id="abc" />);

    fireEvent.click(screen.getByRole("button", { name: "Put back" }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch.mock.calls[0][0]).toBe("/v1/evidence/abc/not-a-transaction");
    expect(fetch.mock.calls[0][1]).toEqual({ method: "DELETE" });
  });

  it("says why it did not work", async () => {
    respond(422, {
      error: { message: "This is not marked as not a transaction." },
    });
    render(<PutBack id="abc" />);

    fireEvent.click(screen.getByRole("button", { name: "Put back" }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "This is not marked as not a transaction.",
      ),
    );
    expect(router.refresh).not.toHaveBeenCalled();
  });
});
