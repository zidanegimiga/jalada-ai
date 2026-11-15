import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { MatchCard } from "./match-card";
import { entry, matchItem } from "./test-data";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

function respond(status: number, body: unknown) {
  const text = status === 204 ? null : JSON.stringify(body);
  const fetch = vi.fn().mockResolvedValue(new Response(text, { status }));
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("MatchCard", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("shows the payment and the receipt side by side, with why they may match", () => {
    render(<MatchCard item={matchItem()} />);

    expect(
      screen.getByText("We found a receipt that may belong to this payment"),
    ).toBeInTheDocument();
    expect(screen.getByText("M-PESA CARD · 5 Nov 2026")).toBeInTheDocument();
    expect(
      screen.getByText("SAMPLE MUSIC SHOP · 5 Nov 2026"),
    ).toBeInTheDocument();
    expect(screen.getByText("Same amount, same day")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "See receipt" })).toHaveAttribute(
      "href",
      "/v1/evidence/receipt-1/file",
    );
  });

  it("joins them when the user says they are the same purchase", async () => {
    const fetch = respond(200, entry());
    render(<MatchCard item={matchItem()} />);

    fireEvent.click(screen.getByRole("button", { name: "Yes, same purchase" }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch.mock.calls[0][0]).toBe("/v1/suggestions/suggestion-1/accept");
  });

  it("keeps them apart when the user says they are not", async () => {
    const fetch = respond(204, null);
    render(<MatchCard item={matchItem()} />);

    fireEvent.click(screen.getByRole("button", { name: "Not the same" }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch.mock.calls[0][0]).toBe("/v1/suggestions/suggestion-1/decline");
  });

  it("says why an answer did not save", async () => {
    respond(404, {
      error: { message: "That question has no answer to give any more." },
    });
    render(<MatchCard item={matchItem()} />);

    fireEvent.click(screen.getByRole("button", { name: "Not the same" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "That question has no answer to give any more.",
    );
    expect(router.refresh).not.toHaveBeenCalled();
  });
});
