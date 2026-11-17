import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { HowPaidCard } from "@/features/review/components/HowPaidCard";
import { entry, receiptItem } from "../support/review-fixtures";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

function respond(status: number, body: unknown) {
  const fetch = vi
    .fn()
    .mockResolvedValue(new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("HowPaidCard", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("shows the receipt and asks how it was paid", () => {
    render(<HowPaidCard item={receiptItem()} />);

    expect(screen.getByText("KSh 419.00")).toBeInTheDocument();
    expect(
      screen.getByText(
        "No payment message came for this receipt. How did you pay?",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "See receipt" })).toHaveAttribute(
      "href",
      "/v1/evidence/receipt-1/file",
    );
  });

  it.each([
    ["Cash", "cash"],
    ["Card", "card"],
  ])("sends the answer %s", async (button, paidWith) => {
    const fetch = respond(200, entry({ status: "needs_review" }));
    render(<HowPaidCard item={receiptItem()} />);

    fireEvent.click(screen.getByRole("button", { name: button }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch.mock.calls[0][0]).toBe("/v1/receipts/candidate-1/paid");
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
      paid_with: paidWith,
    });
  });
});
