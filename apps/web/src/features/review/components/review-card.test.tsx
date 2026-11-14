import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ReviewCard } from "./review-card";
import { CATEGORIES, entry, item } from "./test-data";

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
    expect(screen.getByRole("link", { name: "See original" })).toHaveAttribute(
      "href",
      "/v1/evidence/evidence-1/file",
    );
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

    fireEvent.change(screen.getByLabelText("What it was for"), {
      target: { value: "personal_food" },
    });
    fireEvent.submit(screen.getByRole("button", { name: "Add to ledger" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Add the amount before confirming.",
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
});
