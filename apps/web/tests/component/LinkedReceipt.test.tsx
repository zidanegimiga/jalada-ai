import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LinkedReceipt } from "@/features/review/components/LinkedReceipt";
import { entry, matchItem } from "../support/review-fixtures";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

const match = matchItem().match!;

describe("LinkedReceipt", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("names the receipt and links to it", () => {
    render(<LinkedReceipt match={match} />);

    expect(
      screen.getByText(/Receipt from SAMPLE MUSIC SHOP is linked/),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "See receipt" })).toHaveAttribute(
      "href",
      "/v1/evidence/receipt-1/file",
    );
  });

  it("takes the match back", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify(entry()), { status: 200 }),
      );
    vi.stubGlobal("fetch", fetch);
    render(<LinkedReceipt match={match} />);

    fireEvent.click(screen.getByRole("button", { name: "Undo" }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch.mock.calls[0][0]).toBe("/v1/suggestions/suggestion-1/undo");
  });
});
