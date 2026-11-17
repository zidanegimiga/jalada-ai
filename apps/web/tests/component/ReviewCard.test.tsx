import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ReviewCard } from "@/features/review/components/ReviewCard";
import { chooseOption } from "../support/choose";
import { CATEGORIES, entry, item, matchItem } from "../support/review-fixtures";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

function respond(status: number, body: unknown) {
  const text = status === 204 ? null : JSON.stringify(body);
  const fetch = vi.fn().mockResolvedValue(new Response(text, { status }));
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("ReviewCard", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("shows the amount, who and when, and the proposed category", () => {
    render(<ReviewCard item={item(entry())} categories={CATEGORIES} />);

    expect(screen.getByText("KSh 150.00")).toBeInTheDocument();
    expect(screen.getByText("JANE WANJIKU · 4 Nov 2026")).toBeInTheDocument();
    expect(screen.getByText("Food")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "See original" }),
    ).toHaveAttribute("aria-haspopup", "dialog");
  });

  it("shows a receipt the user linked to the payment", () => {
    const linked = { ...item(entry()), linked_receipt: matchItem().match };
    render(<ReviewCard item={linked} categories={CATEGORIES} />);

    expect(screen.getByRole("button", { name: "Undo" })).toBeInTheDocument();
  });

  it("asks if a paybill payment went to my own account", () => {
    const asked = {
      ...item(entry({ category: null, category_name: null })),
      ask_own_account: true,
    };
    render(<ReviewCard item={asked} categories={CATEGORIES} />);

    expect(screen.getByText(/Is this your own account\?/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Yes, it is my account" }),
    ).toBeInTheDocument();
  });

  it("shows the own account of a transfer, with Undo", () => {
    const moved = {
      ...item(entry({ category: "own_transfer_out" })),
      own_account: "SAMPLE BANK PAYBILL ending 6789",
    };
    render(<ReviewCard item={moved} categories={CATEGORIES} />);

    expect(
      screen.getByText("To your own account, SAMPLE BANK PAYBILL ending 6789."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Undo" })).toBeInTheDocument();
  });

  it("confirms with one tap", async () => {
    const fetch = respond(200, entry({ status: "confirmed" }));
    render(<ReviewCard item={item(entry())} categories={CATEGORIES} />);

    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch.mock.calls[0][0]).toBe("/v1/entries/entry-1/confirm");
  });

  it("asks for a category before confirming when there is none", () => {
    render(
      <ReviewCard
        item={item(entry({ category: null, category_name: null }))}
        categories={CATEGORIES}
      />,
    );

    expect(
      screen.getByText("We could not tell what this was for."),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));

    expect(screen.getByLabelText("What it was for")).toBeInTheDocument();
  });

  it("opens the form straight away for evidence nothing could read", () => {
    render(<ReviewCard item={item(null)} categories={CATEGORIES} />);

    expect(screen.getByText("Amount not read")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Add to ledger" }),
    ).toBeInTheDocument();
  });

  it("shows why a save was refused", async () => {
    respond(422, {
      error: {
        code: "invalid_entry",
        message: "Add the amount before confirming.",
      },
    });
    render(<ReviewCard item={item(null)} categories={CATEGORIES} />);

    await chooseOption("What it was for", "Food");
    fireEvent.submit(screen.getByRole("button", { name: "Add to ledger" }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Add the amount before confirming.",
      ),
    );
    expect(router.refresh).not.toHaveBeenCalled();
  });

  it("asks once before marking it not a transaction", async () => {
    const fetch = respond(204, null);
    render(<ReviewCard item={item(entry())} categories={CATEGORIES} />);

    fireEvent.click(screen.getByRole("button", { name: "Not a transaction" }));
    expect(fetch).not.toHaveBeenCalled();
    expect(
      screen.getByText(/This will not be counted anywhere/),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Not a transaction" }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch.mock.calls[0][0]).toBe(
      "/v1/evidence/evidence-1/not-a-transaction",
    );
  });

  it("keeps the item when the user changes their mind", () => {
    const fetch = respond(204, null);
    render(<ReviewCard item={item(entry())} categories={CATEGORIES} />);

    fireEvent.click(screen.getByRole("button", { name: "Not a transaction" }));
    fireEvent.click(screen.getByRole("button", { name: "Keep it" }));

    expect(fetch).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: "Not a transaction" }),
    ).toBeInTheDocument();
  });

  it("offers a model's category as a suggestion to accept or change", async () => {
    const fetch = respond(200, entry({ status: "confirmed" }));
    render(
      <ReviewCard
        item={item(entry({ category_suggested: true }))}
        categories={CATEGORIES}
      />,
    );

    expect(
      screen.getByText("Suggested: Food. Is that right?"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Yes, confirm" }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch.mock.calls[0][0]).toBe("/v1/entries/entry-1/confirm");
  });
});
